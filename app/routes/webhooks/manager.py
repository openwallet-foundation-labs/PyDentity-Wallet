from flask import current_app

from .models import Message, CredentialOffer, PresentationRequest, Notification, Connection
from app.plugins import AskarStorage, AgentController, AskarStorageKeys
askar = AskarStorage()
agent = AgentController()

class WebhookManager:
    def __init__(self, wallet_id: str):
        # Dictionary mapping topic names to handler methods
        self.wallet_id = wallet_id
        self.topic_handlers = {
            'connections': self.topic_connections,
            'out_of_band': self.topic_out_of_band,
            'ping': self.topic_ping,
            'basicmessages': self.topic_basicmessages,
            'issue_credential': self.topic_issue_credential,
            'issuer_cred_rev': self.topic_issuer_cred_rev,
            'issue_credential_v2_0': self.topic_issue_credential_v2_0,
            'issue_credential_v2_0_anoncreds': self.topic_issue_anoncreds,
            'present_proof': self.topic_present_proof,
            'present_proof_v2_0': self.topic_present_proof_v2_0,
            'revocation_registry': self.topic_revocation_registry,
        }

    async def handle_topic(self, topic, payload):
        """Handle a webhook topic by invoking the appropriate handler method"""
        current_app.logger.info(f'Processing webhook topic: {topic}')
        if not (topic_handle := self.topic_handlers.get(topic)):
            raise ValueError(f"Invalid topic: {topic}")
        
        return await topic_handle(payload)

    async def _null(self, payload):
        current_app.logger.info('____NULL____')
        current_app.logger.info(payload)    
        return {}, 200

    async def topic_basicmessages(self, payload):
        if payload.get('state') == 'received':
            entry = Message(
                content=payload.get('content'),
                timestamp=payload.get('sent_time'),
                inbound=True
            ).model_dump()
            await askar.append('messages', payload.get('connection_id'), entry)
            
            wallet = await askar.fetch('wallet', self.wallet_id)
            
            agent.set_token(wallet['token'])
            
            connection = agent.get_connection_info(payload.get('connection_id'))
            sender_name = connection.get('their_label')
            notification = Notification(
                type='connection',
                title=f'New message from {sender_name}',
                details=entry
            ).model_dump()
            await askar.append('notifications', self.wallet_id, connection)
        else:
            current_app.logger.warning(payload.get('state'))
        return {}, 200

    async def topic_connections(self, connection):
        state = connection.get('state')
        connection_id = connection.get('connection_id')
        current_app.logger.info(f'Connection {connection_id}: {state}')
        
        connection = Connection(
            active=connection.get('state') == 'active',
            state=connection.get('state'),
            created=connection.get('created_at'),
            updated=connection.get('updated_at'),
            connection_id=connection.get('connection_id'),
            label=connection.get('their_label'),
            did=connection.get('their_did')
        ).model_dump()
        tags = {
            'wallet_id': self.wallet_id,
            'connection_id': connection.get('connection_id')
        }
        if state == 'invitation':
            if not await askar.fetch_entry_by_tag(AskarStorageKeys.CONNECTIONS, tags):
                await askar.append(AskarStorageKeys.CONNECTIONS, self.wallet_id, connection)
                await askar.store(AskarStorageKeys.CONNECTIONS, tags['connection_id'], connection, tags)
                
        elif state == 'request':
            pass
        elif state == 'response':
            pass
        elif state == 'active':
            # their_label = connection.get('their_label')
            # notification = Notification(
            #     type='connection',
            #     title=f'New connection with {their_label}',
            #     details=connection
            # ).model_dump()
            # await askar.append(AskarStorageKeys.NOTIFICATIONS, self.wallet_id, notification)
            await askar.update(AskarStorageKeys.CONNECTIONS, tags['connection_id'], connection, tags)
        else:
            pass
        return {}, 200

    async def topic_out_of_band(self, payload):
        """Handle out-of-band invitation webhooks"""
        current_app.logger.info('Out of band state: ' + payload.get('state'))
        if payload.get('state') == 'initial':
            pass
        elif payload.get('state') == 'done':
            pass
        elif payload.get('state') == 'deleted':
            pass
        else:
            pass
        return {}, 200

    async def topic_ping(self, payload):
        """Handle ping webhooks"""
        current_app.logger.info('Ping received')
        return {"status": "pong"}, 200
    
    async def topic_issue_credential(self, payload):
        """Handle issue credential webhooks"""
        current_app.logger.warning(payload.get('state'))
        if payload.get('state') == 'offer-received':
            pass
        return {}, 200

    async def topic_issuer_cred_rev(self, payload):
        """Handle issuer credential revocation webhooks"""
        current_app.logger.info('Issuer credential revocation state: ' + payload.get('state'))
        # Add revocation logic here as needed
        return {}, 200

    async def topic_issue_credential_v2_0(self, exchange):
        """Handle issue credential v2.0 webhooks"""
        current_app.logger.warning(f"=== CREDENTIAL OFFER WEBHOOK ===")
        current_app.logger.warning(f"State: {exchange.get('state')}")
        current_app.logger.warning(f"Cred Ex ID: {exchange.get('cred_ex_id')}")
        current_app.logger.warning(f"Connection ID: {exchange.get('connection_id')}")
        # current_app.logger.warning(f"Full payload: {payload}")
                
        cred_offer = CredentialOffer(
            state=exchange.get('state'),
            completed=exchange.get('state') == 'done',
            timestamp=exchange.get('created_at'),
            exchange_id=exchange.get('cred_ex_id'),
            connection_id=exchange.get('connection_id'),
            # comment=exchange.get('cred_offer').get('comment'),
            # preview=preview,
        ).model_dump()
        
        if exchange.get('state') == 'offer-received':
            current_app.logger.info(f"Processing credential offer for wallet: {self.wallet_id}")
            
            wallet = await askar.fetch(AskarStorageKeys.WALLETS, self.wallet_id)
            if not wallet:
                current_app.logger.error(f"Wallet not found: {self.wallet_id}")
                return {}, 404
                
            agent.set_token(wallet['token'])
            
            cred_ex = agent.get_credential_exchange_info(
                exchange.get('cred_ex_id')
            ).get('cred_ex_record')
            
            current_app.logger.info(f"Credential exchange record: {cred_ex}")
            cred_offer['comment'] = cred_ex.get('cred_offer').get('comment')
            
            preview = {}
            for attribute in cred_ex.get('cred_offer').get('credential_preview').get('attributes'):
                preview[attribute.get('name')] = attribute.get('value')
            
            current_app.logger.info(f"Credential preview attributes: {preview}")
            cred_offer['preview'] = preview
            
            current_app.logger.info(f"Storing credential offer to CRED_OFFERS: {cred_offer}")
            await askar.append(AskarStorageKeys.CRED_OFFERS, self.wallet_id, cred_offer)
            
            # schema_name = agent.get_schema_info(
            #     exchange.get('by_format').get('cred_offer').get('anoncreds').get('schema_id')
            # ).get('schema').get('name')
            schema_name = 'Schema Name'
            issuer_name = agent.get_connection_info(
                exchange.get('connection_id')
            ).get('their_label')
            
            current_app.logger.info(f"Schema name: {schema_name}, Issuer: {issuer_name}")
            
            notification = Notification(
                type='cred_offer',
                title=f'{issuer_name} is offering {schema_name}',
                details=cred_offer
            ).model_dump()
            
            current_app.logger.info(f"Creating notification: {notification}")
            await askar.append(AskarStorageKeys.NOTIFICATIONS, self.wallet_id, notification)
            current_app.logger.info(f"✅ Credential offer notification created successfully!")
            
            
            # agent = AgentController()
            # wallet = await askar.fetch('wallet', self.wallet_id)
            # agent.set_token(wallet['token'])
            # preview = {}
            # for attribute in payload.get('cred_offer').get('credential_preview').get('attributes'):
            #     preview[attribute.get('name')] = attribute.get('value')
            # await askar.append('cred_ex', payload.get('connection_id'), cred_offer)
            
            # schema_id = payload.get('by_format').get('cred_offer').get('anoncreds').get('schema_id')
            # cred_def_id = payload.get('by_format').get('cred_offer').get('anoncreds').get('cred_def_id')
            
            # wallet = await askar.fetch('wallet', self.wallet_id)
            
            # agent.set_token(wallet['token'])
            # connection = agent.get_connection_info(payload.get('connection_id'))
            # schema = agent.get_schema_info(schema_id).get('schema')
            # issuer_name = connection.get('their_label')
            # cred_name = schema.get('name')
            # cred_meta = {
            #     'issuer_name': issuer_name,
            #     'issuer_image': '',
            #     'cred_name': schema.get('name'),
            #     'cred_version': schema.get('version'),
            # }
            # await askar.store('cred_meta', cred_def_id, cred_meta)
            
        elif exchange.get('state') == 'request-sent':
            pass
        elif exchange.get('state') == 'credential-received':
            pass
        elif exchange.get('state') == 'done':
            pass
        #     attributes = payload.get('cred_offer').get('credential_preview').get('attributes')
        #     cred_input = {
        #         'cred_def_id': payload.get('by_format').get('cred_offer').get('anoncreds').get('cred_def_id'),
        #         'attrs': {}
        #     }
        #     for attribute in attributes:
        #         cred_input[attribute['name']] = attribute['value']
        #     # Note: beautify_anoncreds function would need to be imported if used
        #     # credential = await beautify_anoncreds(cred_input)
        #     # current_app.logger.warning(credential)
        #     # await askar.append('credentials', self.wallet_id, credential)
        # else:
        #     current_app.logger.warning(payload.get('state'))
        return {}, 200

    async def topic_issue_anoncreds(self, payload):
        return {}, 200

    async def topic_present_proof(self, payload):
        """Handle present proof webhooks"""
        current_app.logger.warning(payload.get('state'))
        if payload.get('state') == 'offer-received':
            pass
        return {}, 200

    async def topic_present_proof_v2_0(self, payload):
        """Handle present proof v2.0 webhooks"""
        if payload.get('state') == 'request-received':
            pres_req = PresentationRequest(
                timestamp=payload.get('created_at'),
                exchange_id=payload.get('pres_ex_id'),
                connection_id=payload.get('connection_id'),
                attributes=payload.get('by_format').get('pres_request').get('anoncreds').get('requested_attributes'),
                predicates=payload.get('by_format').get('pres_request').get('anoncreds').get('requested_predicates')
            ).model_dump()
            await askar.append('pres_ex', payload.get('connection_id'), pres_req)
            
            wallet = await askar.fetch('wallet', self.wallet_id)
            
            agent.set_token(wallet['token'])
            connection = agent.get_connection_info(payload.get('connection_id'))
            
            verifier_name = connection.get('their_label')
            pres_name = payload.get('by_format').get('pres_request').get('anoncreds').get('name')
            notification = Notification(
                type='pres_request',
                title=f'{verifier_name} is requesting {pres_name}',
                details=pres_req
            ).model_dump()
            await askar.append('notifications', self.wallet_id, notification)
        elif payload.get('state') == 'presentation-sent':
            pass
        elif payload.get('state') == 'done':
            pass
        return {}, 200

    async def topic_revocation_registry(self, payload):
        """Handle revocation registry webhooks"""
        current_app.logger.info('Revocation registry state: ' + payload.get('state'))
        # Add revocation registry logic here as needed
        return {}, 200