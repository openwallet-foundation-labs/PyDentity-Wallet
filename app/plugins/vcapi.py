import requests
import uuid
import json
from datetime import datetime
from app.plugins.acapy import AgentController
from app.plugins.askar import AskarStorage
from app.models.notification import Notification

agent = AgentController()
askar = AskarStorage()

class VcApiExchanger:
    def __init__(self, wallet_id=None, exchange_url=None):
        self.wallet_id = wallet_id
        self.exchange_url = exchange_url
    
    def initiate_exchange(self):
        r = requests.post(self.exchange_url, json={})
        return r.json()
    
    async def store_credential(self, vp):
        wallet = await askar.fetch("wallet", self.wallet_id)
        for vc in vp.get('verifiableCredential'):
            
            agent.set_token(
                agent.request_token(self.wallet_id, wallet.get('wallet_key')).get('token')
            )
            
            # TODO, verify credential & remove unverifiable proofs
            # We store the VC in the cloud agent
            agent.store_credential(vc)
            
            # We store the VC in the server store
            await askar.append("credentials", self.wallet_id, vc)
        
            # We create an event notification
            notification = Notification(
                id=str(uuid.uuid4()),
                type='vcapi_exchange',
                title='Credential Stored',
                origin=vc['issuer'] if isinstance(vc['issuer'], str) else vc['issuer']['id'],
                message='Credential Stored',
                timestamp=str(datetime.now().isoformat())
            )
            await askar.append("notifications", self.wallet_id, notification)
    
    async def present_credential(self, vpr):
        wallet = await askar.fetch("wallet", self.wallet_id)
        
        # Start building presentation object
        presentation = {
            '@context': ['https://www.w3.org/ns/credentials/v2'],
            'type': ['VerifiablePresentation'],
        }
        
        # Define proof options
        proof_options = {
            # TODO, how to select cryptosuite? Default to 'Ed25519Signature2020' for now
            'proofType': 'Ed25519Signature2020',
            'domain': vpr.get('domain'),
            'challenge': vpr.get('challenge'),
            'proofPurpose': 'authentication',
        }
        
        # TODO, implement tag query for credential selection
        # Get all credentials from wallet
        credentials = await askar.fetch("credentials", self.wallet_id)
        for query in vpr.get('query'):
            if query.get('type') == 'DIDAuthentication':
                
                methods = [method['method'] for method in query.get('acceptedMethods')]
                
                # TODO, only DID key for now, add support for did web
                if 'key' not in methods:
                    return
                
                presentation['holder'] = wallet['holder_id']
                multikey = presentation['holder'].split(':')[-1]
                proof_options['verificationMethod'] = f'did:key:{multikey}#{multikey}'
                
            if query.get('type') == 'QueryByExample':
                
                # We add the verifiableCredential property if not present
                if not presentation.get('verifiableCredential'):
                    presentation['verifiableCredential'] = []

                cred_queries = query.get('credentialQuery')
                cred_queries = cred_queries if isinstance(cred_queries, list) else [cred_queries]
                for cred_query in cred_queries:

                    # Check if the requested credential is required, ignore if optional...
                    if not cred_query.get('required', True):
                        continue
                    
                    # TODO, process required trusted issuers
                    # trusted_issuers = cred_query.get('trustedIssuer', [])
                    reason = cred_query.get('reason')
                    example = cred_query.get('example')
                    accepted_cryptosuites = cred_query.get('acceptedCryptosuites')
                    
                    # TODO, more comprehensive selection might be needed
                    vc = next((credential for credential in credentials
                            if set(example['type']).issubset(credential['type']) 
                            and set(example['@context']).issubset(credential['@context'])
                    ), None)
                    
                    # We remove the proofs and force into an array
                    proofs = vc.pop('proof')
                    proofs = proofs if isinstance(proofs, list) else [proofs]
                    
                    # We filter out proofs which don't have an accepted cryptosuite
                    for proof in proofs:
                        if proof.get('type') == 'Ed25519Signature2020' and 'Ed25519Signature2020' not in accepted_cryptosuites:
                            proofs.remove(proof)
                        elif proof.get('type') == 'DataIntegrityProof' and proof.get('cryptosuite') not in accepted_cryptosuites:
                            proofs.remove(proof)
                        
                    # We abandon the exchange if no proof is left
                    if len(proofs) == 0:
                        continue
                    
                    # We select the first filtered proof to include in the presentation
                    vc['proof'] = proofs[0]
                        
                    # We append our credential matching the requested query
                    presentation['verifiableCredential'].append(vc)
                    
                    # We move onto the next query
                    continue
                
        # We sign the presentation
        agent.set_token(
            agent.request_token(self.wallet_id, wallet.get('wallet_key')).get('token')
        )
        vp = agent.sign_presentation(presentation, proof_options).get('verifiablePresentation')
                
        # We send the verifiable presentation to the exchange endpoint
        r = requests.post(self.exchange_url, json={'verifiablePresentation': vp})
        
        # If the response fails, we abandon the exchange
        if r.status_code != 200:
            return
        
        # We store an event notification of the presentation exchange
        notification = Notification(
            id=str(uuid.uuid4()),
            type='vcapi_exchange',
            title='Presentation Sent',
            origin=vpr.get('domain'),
            message=reason,
            timestamp=str(datetime.now().isoformat())
        )
        await askar.append("notifications", self.wallet_id, notification)