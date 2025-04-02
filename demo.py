import os
from alith import Agent
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize the Alith Agent
agent = Agent(
    name="Simple Metis Agent",
    model="gpt-4",
    preamble="""You are a helpful AI assistant for Metis L2 blockchain. 
    You can answer questions about blockchain technology, Metis L2, 
    and help users understand basic concepts.""",
)

def main():
    print("🤖 Simple Metis AI Agent is running. Type 'exit' to quit.")
    print("Ask me anything about Metis L2 or blockchain!")
    
    while True:
        # Get user input
        user_input = input("\nYou: ")
        
        # Check if user wants to exit
        if user_input.lower() in ["exit", "quit", "bye"]:
            print("Agent: Goodbye! Have a great day!")
            break
        
        # Get response from the agent
        response = agent.prompt(user_input)
        
        # Print the response
        print(f"Agent: {response}")

if __name__ == "__main__":
    main()
