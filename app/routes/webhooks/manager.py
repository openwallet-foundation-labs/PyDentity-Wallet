from flask import current_app

from .models import Message, CredentialOffer, PresentationRequest, Notification, Connection
from app.plugins import AskarStorage, AgentController, AskarStorageKeys
from app.utils import beautify_anoncreds, notification_broadcaster, create_notification, delete_notification


class WebhookManager:
    def __init__(self, wallet: dict):
        # Dictionary mapping topic names to handler methods
        self.wallet = wallet
        self.wallet_id = wallet.get('wallet_id')
        
        # Initialize agent controller with wallet token
        self.agent = AgentController()
        self.agent.set_token(wallet.get('token'))
        
        # Initialize wallet-specific askar storage
        self.askar = AskarStorage.for_wallet(self.wallet_id)
        
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
            await self.askar.append(AskarStorageKeys.MESSAGES, entry)
            
            connection = self.agent.get_connection_info(payload.get('connection_id'))
            sender_name = connection.get('their_label')
            # Note: notifications are handled by create_notification in utils, not here
            # This old notification code can be removed or updated later
        else:
            current_app.logger.warning(payload.get('state'))
        return {}, 200

    async def topic_connections(self, connection_payload):
        state = connection_payload.get('state')
        connection_id = connection_payload.get('connection_id')
        current_app.logger.info(f'Connection {connection_id}: {state}')
        
        # Get their_label from payload, or fetch from agent if missing
        their_label = connection_payload.get('their_label')
        if not their_label:
            try:
                connection_info = self.agent.get_connection_info(connection_id)
                their_label = connection_info.get('their_label', 'Unknown')
                current_app.logger.info(f"Fetched label from agent: {their_label}")
            except Exception as e:
                current_app.logger.warning(f"Could not fetch connection label: {e}")
                their_label = 'Unknown'
        
        connection = Connection(
            active=connection_payload.get('state') == 'active',
            state=connection_payload.get('state'),
            created=connection_payload.get('created_at'),
            updated=connection_payload.get('updated_at'),
            connection_id=connection_payload.get('connection_id'),
            label=their_label,
            did=connection_payload.get('their_did')
        ).model_dump()
        tags = {
            'connection_id': connection_id,
            'label': their_label,
            'their_label': their_label,
            'state': state,
            'their_did': connection_payload.get('their_did')
        }
        if state == 'invitation':
            # Check if connection already exists in wallet's profile
            connections = await self.askar.fetch(AskarStorageKeys.CONNECTIONS) or []
            if not any(c.get('connection_id') == connection_id for c in connections):
                await self.askar.append(AskarStorageKeys.CONNECTIONS, connection)
                current_app.logger.info(f"Added connection {connection_id} to profile")
                
        elif state == 'request':
            pass
        elif state == 'response':
            pass
        elif state == 'active':
            current_app.logger.info(f"✅ Connection active with: {their_label}")
            
            # Update connection in the array
            connections = await self.askar.fetch(AskarStorageKeys.CONNECTIONS) or []
            for i, conn in enumerate(connections):
                if conn.get('connection_id') == connection_id:
                    connections[i] = connection
                    break
            await self.askar.update(AskarStorageKeys.CONNECTIONS, "data", connections)
            
            # Broadcast connection active event for toast notification
            notification_broadcaster.broadcast(
                self.wallet_id,
                'connection_active',
                {
                    'label': their_label,
                    'connection_id': connection_id
                }
            )
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
            
            cred_ex = self.agent.get_credential_exchange_info(
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
            await self.askar.append(AskarStorageKeys.CRED_OFFERS, cred_offer)
            
            # Get schema name from schema_id
            schema_name = 'Credential'  # Default fallback
            try:
                schema_id = exchange.get('by_format', {}).get('cred_offer', {}).get('anoncreds', {}).get('schema_id')
                if schema_id:
                    current_app.logger.info(f"Fetching schema info for: {schema_id}")
                    schema_info = self.agent.get_schema_info(schema_id)
                    if schema_info and schema_info.get('schema'):
                        schema_name = schema_info['schema'].get('name', 'Credential')
                        current_app.logger.info(f"Found schema name: {schema_name}")
                    else:
                        current_app.logger.warning(f"Schema info returned but no 'schema' key found")
                else:
                    current_app.logger.warning(f"No schema_id found in exchange")
            except Exception as e:
                current_app.logger.error(f"Error fetching schema info: {e}", exc_info=True)
                # Keep default fallback value
            
            issuer_name = self.agent.get_connection_info(
                exchange.get('connection_id')
            ).get('their_label')
            
            current_app.logger.info(f"Schema name: {schema_name}, Issuer: {issuer_name}")
            
            # Create notification using new individual storage system
            notification = await create_notification(
                wallet_id=self.wallet_id,
                notification_id=exchange.get('cred_ex_id'),
                notification_type='cred_offer',
                title=f'{issuer_name} is offering {schema_name}',
                details=cred_offer
            )
            
            current_app.logger.info(f"✅ Credential offer notification created: {notification['id']}")
            
            # Broadcast real-time notification to connected clients
            notification_broadcaster.broadcast(
                self.wallet_id,
                'notification_created',
                {
                    'notification_type': 'cred_offer',
                    'title': notification['title'],
                    'exchange_id': exchange.get('cred_ex_id')
                }
            )
            
            
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
            current_app.logger.info(f"✅ Credential request sent for exchange: {exchange.get('cred_ex_id')}")
            
            # Delete the notification using the new system
            deleted = await delete_notification(self.wallet_id, exchange.get('cred_ex_id'))
            
            if deleted:
                # Broadcast notification removal
                notification_broadcaster.broadcast(
                    self.wallet_id,
                    'notification_removed',
                    {'exchange_id': exchange.get('cred_ex_id')}
                )
            
        elif exchange.get('state') == 'credential-received':
            current_app.logger.info(f"📥 Credential received for exchange: {exchange.get('cred_ex_id')}")
        
        elif exchange.get('state') == 'declined' or exchange.get('state') == 'abandoned':
            current_app.logger.info(f"❌ Credential offer declined/abandoned: {exchange.get('cred_ex_id')}")
            
            # Delete the notification using the new system
            deleted = await delete_notification(self.wallet_id, exchange.get('cred_ex_id'))
            
            if deleted:
                # Broadcast notification removal
                notification_broadcaster.broadcast(
                    self.wallet_id,
                    'notification_removed',
                    {'exchange_id': exchange.get('cred_ex_id'), 'reason': 'declined'}
                )
            
        elif exchange.get('state') == 'done':
            current_app.logger.info(f"=== CREDENTIAL ISSUED (DONE STATE) ===")
            current_app.logger.info(f"Exchange ID: {exchange.get('cred_ex_id')}")
            
            # Get the full credential exchange info
            cred_ex = self.agent.get_credential_exchange_info(
                exchange.get('cred_ex_id')
            )
            
            current_app.logger.info(f"Full credential exchange: {cred_ex}")
            
            # Store the credential
            cred_record = cred_ex.get('cred_ex_record', {})
            
            # Extract credential attributes
            attributes = {}
            if cred_offer := cred_record.get('cred_offer'):
                if preview := cred_offer.get('credential_preview'):
                    for attr in preview.get('attributes', []):
                        attributes[attr.get('name')] = attr.get('value')
            
            # Get schema and credential definition info
            by_format = exchange.get('by_format', {})
            anoncreds_offer = by_format.get('cred_offer', {}).get('anoncreds', {})
            schema_id = anoncreds_offer.get('schema_id')
            cred_def_id = anoncreds_offer.get('cred_def_id')
            
            # Get schema info (name and version)
            schema_name = 'Credential'
            schema_version = None
            if schema_id:
                try:
                    schema_info = self.agent.get_schema_info(schema_id)
                    if schema_info and schema_info.get('schema'):
                        schema_name = schema_info['schema'].get('name', 'Credential')
                        schema_version = schema_info['schema'].get('version')
                except Exception as e:
                    current_app.logger.warning(f"Could not fetch schema info: {e}")
            
            # Get credential definition info (tag)
            cred_def_tag = None
            if cred_def_id:
                try:
                    cred_def_info = self.agent.get_cred_def_info(cred_def_id)
                    if cred_def_info and cred_def_info.get('credential_definition'):
                        cred_def_tag = cred_def_info['credential_definition'].get('tag')
                except Exception as e:
                    current_app.logger.warning(f"Could not fetch cred def info: {e}")
            
            # Get issuer info (connection label and issuer DID)
            connection_label = None
            issuer_id = None
            if connection_id := exchange.get('connection_id'):
                try:
                    connection_info = self.agent.get_connection_info(connection_id)
                    connection_label = connection_info.get('their_label')
                    # Try to get issuer DID from connection
                    issuer_id = connection_info.get('their_did')
                except Exception as e:
                    current_app.logger.warning(f"Could not fetch connection info: {e}")
            
            # Build credential using beautify_anoncreds to create W3C VC format
            credential, tags = beautify_anoncreds(
                attributes=attributes,
                schema_id=schema_id,
                schema_name=schema_name,
                schema_version=schema_version,
                cred_def_id=cred_def_id,
                cred_def_tag=cred_def_tag,
                issuer_id=issuer_id,
                connection_label=connection_label,
                issuer_image=None,
                created_at=exchange.get('created_at'),
                cred_ex_id=exchange.get('cred_ex_id')
            )
            
            current_app.logger.info(f"Storing credential: {credential.get('name')} (ex_id: {exchange.get('cred_ex_id')})")
            
            # Delete the notification (in case request-sent webhook didn't fire)
            await delete_notification(self.wallet_id, exchange.get('cred_ex_id'))
            
            # Check for duplicates before storing (by credential ID)
            existing_credentials = await self.askar.fetch(AskarStorageKeys.CREDENTIALS) or []
            
            # Look for duplicate by credential ID (urn:uuid:{cred_ex_id})
            credential_id = credential.get('id')
            is_duplicate = any(
                cred.get('id') == credential_id
                for cred in existing_credentials
            ) if credential_id else False
            
            if is_duplicate:
                current_app.logger.warning(f"⚠️ Duplicate credential detected (id: {credential_id}), skipping storage")
            else:
                # Store the credential with tags
                await self.askar.append(AskarStorageKeys.CREDENTIALS, credential)
                current_app.logger.info(f"✅ Credential stored successfully with tags: {tags}")
            
            # Broadcast single combined event that triggers page reload
            current_app.logger.info(f"📢 Broadcasting credential_received event to wallet: {self.wallet_id}")
            notification_broadcaster.broadcast(
                self.wallet_id,
                'credential_received',
                {
                    'credential_name': schema_name,
                    'issuer_name': connection_label or 'Unknown Issuer',
                    'exchange_id': exchange.get('cred_ex_id'),
                    'notification_removed': True
                }
            )
            current_app.logger.info(f"✅ Broadcast complete")
            
        else:
            current_app.logger.warning(f"Unhandled state: {exchange.get('state')}")
        return {}, 200

    async def topic_issue_anoncreds(self, payload):
        """Handle anoncreds-specific issue credential webhooks"""
        current_app.logger.info(f"=== ANONCREDS CREDENTIAL WEBHOOK ===")
        current_app.logger.info(f"Wallet ID: {self.wallet_id}")
        current_app.logger.info(f"State: {payload.get('state')}")
        current_app.logger.info(f"Cred Ex ID: {payload.get('cred_ex_id')}")
        current_app.logger.info(f"Connection ID: {payload.get('connection_id')}")
        current_app.logger.info(f"Role: {payload.get('role')}")
        current_app.logger.info(f"Initiator: {payload.get('initiator')}")
        
        # Log format-specific data
        if by_format := payload.get('by_format'):
            current_app.logger.info(f"By Format Keys: {by_format.keys()}")
            
            if cred_offer := by_format.get('cred_offer', {}).get('anoncreds'):
                current_app.logger.info(f"--- Anoncreds Offer Data ---")
                current_app.logger.info(f"Schema ID: {cred_offer.get('schema_id')}")
                current_app.logger.info(f"Cred Def ID: {cred_offer.get('cred_def_id')}")
                current_app.logger.info(f"Key Correctness Proof: {bool(cred_offer.get('key_correctness_proof'))}")
                current_app.logger.info(f"Nonce: {cred_offer.get('nonce')}")
            
            if cred_proposal := by_format.get('cred_proposal', {}).get('anoncreds'):
                current_app.logger.info(f"--- Anoncreds Proposal Data ---")
                current_app.logger.info(f"Schema ID: {cred_proposal.get('schema_id')}")
                current_app.logger.info(f"Cred Def ID: {cred_proposal.get('cred_def_id')}")
            
            if cred_request := by_format.get('cred_request', {}).get('anoncreds'):
                current_app.logger.info(f"--- Anoncreds Request Data ---")
                current_app.logger.info(f"Entropy: {cred_request.get('entropy')}")
                current_app.logger.info(f"Cred Def ID: {cred_request.get('cred_def_id')}")
            
            if cred_issue := by_format.get('cred_issue', {}).get('anoncreds'):
                current_app.logger.info(f"--- Anoncreds Issue Data ---")
                current_app.logger.info(f"Schema ID: {cred_issue.get('schema_id')}")
                current_app.logger.info(f"Cred Def ID: {cred_issue.get('cred_def_id')}")
                current_app.logger.info(f"Rev Reg ID: {cred_issue.get('rev_reg_id')}")
                current_app.logger.info(f"Witness: {bool(cred_issue.get('witness'))}")
        
        # Log credential exchange record if present
        if cred_ex_record := payload.get('cred_ex_record'):
            current_app.logger.info(f"--- Credential Exchange Record ---")
            current_app.logger.info(f"Record State: {cred_ex_record.get('state')}")
            current_app.logger.info(f"Thread ID: {cred_ex_record.get('thread_id')}")
            
            if cred_offer_dict := cred_ex_record.get('cred_offer'):
                current_app.logger.info(f"Cred Offer Comment: {cred_offer_dict.get('comment')}")
                if preview := cred_offer_dict.get('credential_preview'):
                    attrs = preview.get('attributes', [])
                    current_app.logger.info(f"Credential Attributes Count: {len(attrs)}")
                    for attr in attrs:
                        current_app.logger.info(f"  - {attr.get('name')}: {attr.get('value')}")
        
        current_app.logger.info(f"Full Payload: {payload}")
        current_app.logger.info(f"=== END ANONCREDS WEBHOOK ===")
        
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
            connection_id = payload.get('connection_id')
            pres_req = PresentationRequest(
                timestamp=payload.get('created_at'),
                exchange_id=payload.get('pres_ex_id'),
                connection_id=connection_id,
                attributes=payload.get('by_format').get('pres_request').get('anoncreds').get('requested_attributes'),
                predicates=payload.get('by_format').get('pres_request').get('anoncreds').get('requested_predicates')
            ).model_dump()
            await self.askar.append(AskarStorageKeys.PRES_REQUESTS, pres_req)
            
            verifier_label = self.agent.get_connection_info(connection_id).get('their_label') if connection_id else 'Unknown Verifier'
            pres_name = payload.get('by_format').get('pres_request').get('anoncreds').get('name')
            
            # Create notification using new individual storage system
            notification = await create_notification(
                wallet_id=self.wallet_id,
                notification_id=payload.get('pres_ex_id'),
                notification_type='pres_request',
                title=f'{verifier_label} is requesting {pres_name}',
                details=pres_req
            )
            
            current_app.logger.info(f"✅ Presentation request notification created: {payload.get('pres_ex_id')}")
            
            # Broadcast notification to UI via SSE
            current_app.logger.info(f"📢 Broadcasting notification_created event to wallet: {self.wallet_id}")
            notification_broadcaster.broadcast(
                self.wallet_id,
                'notification_created',
                {
                    'notification_type': 'pres_request',
                    'title': notification['title'],
                    'exchange_id': payload.get('pres_ex_id')
                }
            )
            current_app.logger.info(f"✅ Broadcast complete for pres_request")
        elif payload.get('state') == 'presentation-sent':
            current_app.logger.info(f"✅ Presentation sent: {payload.get('pres_ex_id')}")
            
            # Delete the notification
            await delete_notification(self.wallet_id, payload.get('pres_ex_id'))
            
            # Broadcast notification removal
            notification_broadcaster.broadcast(
                self.wallet_id,
                'notification_removed',
                {'exchange_id': payload.get('pres_ex_id'), 'reason': 'presentation_sent'}
            )
            
        elif payload.get('state') == 'done':
            current_app.logger.info(f"✅ Presentation verified: {payload.get('pres_ex_id')}")
            
            # Delete the notification (in case presentation-sent didn't fire)
            await delete_notification(self.wallet_id, payload.get('pres_ex_id'))
            
            # Broadcast notification removal
            notification_broadcaster.broadcast(
                self.wallet_id,
                'notification_removed',
                {'exchange_id': payload.get('pres_ex_id'), 'reason': 'presentation_done'}
            )
            
        elif payload.get('state') == 'abandoned' or payload.get('state') == 'declined':
            current_app.logger.info(f"❌ Presentation abandoned/declined: {payload.get('pres_ex_id')}")
            
            # Delete the notification
            await delete_notification(self.wallet_id, payload.get('pres_ex_id'))
            
            # Broadcast notification removal
            notification_broadcaster.broadcast(
                self.wallet_id,
                'notification_removed',
                {'exchange_id': payload.get('pres_ex_id'), 'reason': 'abandoned'}
            )
            
        return {}, 200

    async def topic_revocation_registry(self, payload):
        """Handle revocation registry webhooks"""
        current_app.logger.info('Revocation registry state: ' + payload.get('state'))
        # Add revocation registry logic here as needed
        return {}, 200