from uagents import Agent, Context, Model

# Data model (envelope) which you want to send from one agent to another
class Message(Model):
    message : str

my_first_agent = Agent(
    name = 'My First Agent',
    port = 5050,
    seed = "test_sender_seed_67890",
    endpoint = ['http://localhost:5050/submit']
)

# Address from test_agent_receiver.py output
second_agent = 'agent1q0dleu20px4etcl226mhsqsed7uxmss9uffjgdsv2f62qs9az7f5g4593c4'

@my_first_agent.on_event('startup')
async def startup_handler(ctx : Context):
    ctx.logger.info(f'My name is {ctx.agent.name} and my address is {ctx.agent.address}')
    
    import asyncio
    await asyncio.sleep(3)  # Wait for receiver to be ready
    
    ctx.logger.info(f'Sending message to {second_agent}')
    await ctx.send(second_agent, Message(message = 'Hi Second Agent, this is the first agent.'))
    ctx.logger.info('Message sent!')

if __name__ == "__main__":
    my_first_agent.run()
