import os
import json
import logging

logger = logging.getLogger("CoinbaseAgent")

class CoinbaseAgentWallet:
    """
    Andrew's Sovereign Crypto Wallet.
    Uses Coinbase Developer Platform (CDP) to hold funds in USDC on Base,
    pay for API services automatically, and distribute funds to the owner.
    """
    def __init__(self, data_dir: str = "data/wallets"):
        self.api_key_name = os.getenv("CDP_API_KEY_NAME")
        self.api_key_private_key = os.getenv("CDP_API_KEY_PRIVATE_KEY")
        self.data_dir = data_dir
        
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            
        self.wallet_data_file = os.path.join(self.data_dir, "agent_wallet_seed.json")
        self.cdp_initialized = False
        self._init_cdp()

    def _init_cdp(self):
        """Initializes the CDP SDK if keys are present."""
        if not self.api_key_name or not self.api_key_private_key:
            raise ValueError("CDP API Keys missing. Set CDP_API_KEY_NAME and CDP_API_KEY_PRIVATE_KEY. Andrew, fix configuration.")

        try:
            from cdp import Cdp
            # Ensure the private key has correct line breaks
            private_key = self.api_key_private_key.replace("\\n", "\n")
            Cdp.configure(self.api_key_name, private_key)
            self.cdp_initialized = True
            logger.info("Coinbase CDP SDK Authenticated Successfully.")
            self._ensure_wallet_exists()
        except ImportError:
            logger.error("cdp-sdk is not installed. Run 'pip install cdp-sdk'.")
        except Exception as e:
            logger.error(f"Failed to initialize CDP: {e}")

    def _ensure_wallet_exists(self):
        """Creates a new wallet on Base network if one doesn't exist."""
        if not self.cdp_initialized:
            return
            
        from cdp import Wallet
        
        if os.path.exists(self.wallet_data_file):
            logger.info("Loading existing AI Agent Wallet...")
            with open(self.wallet_data_file, 'r') as f:
                data = json.load(f)
                self.wallet = Wallet.import_data(data)
                logger.info(f"Wallet Loaded. Default Address: {self.wallet.default_address.address_id}")
        else:
            logger.info("Creating a new AI Agent Wallet on Base Network...")
            # We strictly use 'base' network to minimize gas fees to near $0
            self.wallet = Wallet.create(network_id="base")
            with open(self.wallet_data_file, 'w') as f:
                json.dump(self.wallet.export_data(), f)
            logger.info(f"Wallet Created! Address: {self.wallet.default_address.address_id}")

    def get_usdc_balance(self) -> float:
        """Checks the on-chain USDC balance."""
        if not self.cdp_initialized:
            raise RuntimeError("CDP Wallet not initialized. Ensure CDP_API_KEY_NAME and PRIVATE_KEY are set.")
            
        try:
            # CDP returns a string or Decimal, we cast to float
            balance = self.wallet.balance("usdc")
            return float(balance)
        except Exception as e:
            logger.error(f"Failed to fetch USDC balance: {e}")
            raise RuntimeError(f"Failed to fetch USDC balance: {e}")

    def get_wallet_address(self) -> str:
        """Returns the public address for receiving funds."""
        if not self.cdp_initialized:
            raise RuntimeError("CDP Wallet not initialized. Ensure CDP_API_KEY_NAME and PRIVATE_KEY are set.")
        return self.wallet.default_address.address_id

    def execute_payout(self, destination_address: str, amount_usdc: float) -> dict:
        """
        Sends funds from the AI Agent wallet to Donald's personal hardware wallet.
        """
        logger.info(f"Initiating payout of {amount_usdc} USDC to {destination_address}")
        
        if not self.cdp_initialized:
            raise RuntimeError("CDP Wallet not initialized. Ensure CDP_API_KEY_NAME and PRIVATE_KEY are set.")
            
        try:
            current_balance = self.get_usdc_balance()
            if current_balance < amount_usdc:
                return {"status": "error", "message": "Insufficient USDC balance."}
                
            transfer = self.wallet.transfer(amount_usdc, "usdc", destination_address)
            # Wait for transfer to land on-chain
            transfer.wait()
            
            return {
                "status": "success",
                "transaction_hash": transfer.transaction_hash,
                "message": f"Successfully transferred {amount_usdc} USDC on Base."
            }
        except Exception as e:
            logger.error(f"On-chain transfer failed: {e}")
            return {"status": "error", "message": str(e)}

    def fund_api_costs(self, service_name: str, cost_usdc: float) -> dict:
        """
        The Self-Funding Loop. Andrew pays for his own API usage.
        In reality, this would fund a virtual debit card or deposit to a provider's crypto address.
        """
        logger.info(f"Self-Funding: Paying {cost_usdc} USDC for {service_name} API usage.")
        
        stripe_key = os.getenv("STRIPE_SECRET_KEY")
        if stripe_key:
            try:
                import stripe
                stripe.api_key = stripe_key
                # Create a payment intent or invoice
                intent = stripe.PaymentIntent.create(
                    amount=int(cost_usdc * 100),
                    currency="usd",
                    description=f"API Funding for {service_name}"
                )
                return {"status": "success", "intent_id": intent.id}
            except ImportError:
                return {"status": "error", "message": "Stripe not installed."}
            except Exception as e:
                return {"status": "error", "message": str(e)}
        else:
            logger.warning("No STRIPE_SECRET_KEY found. Logging virtual card transaction to DB.")
            return {"status": "simulated", "message": f"Funded {cost_usdc} via internal virtual accounting."}

coinbase_agent = CoinbaseAgentWallet()
