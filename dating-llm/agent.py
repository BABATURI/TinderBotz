
from langchain_google_genai import ChatGoogleGenerativeAI, HarmBlockThreshold, HarmCategory

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage
from tools import get_tools, find_tool_by_name, get_dating_tools
import os
import logging


logger = logging.getLogger(__name__)


with open(".geminikey", "r") as f:
    key = f.read().strip()
    os.environ["GOOGLE_API_KEY"] = key


def run_agent(chain, query):
    messages = [HumanMessage(query)]
    # message_with_image = HumanMessage(
    # content=[
    #     {"type": "text", "text": "Here is an image I want to discuss:"},
    #     {
    #         "type": "image_url",
    #         "image_url": {"url": f"data:image/jpeg;base64,{image_data}"},
    #     },
    # ])
    # message_with_image_url = HumanMessage(
    # content=[
    #     {"type": "text", "text": "Please analyze this image:"},
    #     {"type": "image_url", "image_url": {"url": image_url}},
    # ])



    ai_msg = chain.invoke(messages)
    messages.append(ai_msg)
    print(ai_msg.tool_calls)
    while ai_msg and ai_msg.content == '' and len(messages) < 10:
        if ai_msg.response_metadata['prompt_feedback']['block_reason'] != 0:
            logger.error("Blocked by content filter")
            return
        # For simplicity, we only handle one tool call at a time
        for tool_call in ai_msg.tool_calls:
            logger.debug(f"Tool call: {tool_call}")
            selected_tool = find_tool_by_name(tool_call["name"])
            tool_msg = selected_tool.invoke(tool_call)
            messages.append(tool_msg)
            

        ai_msg = chain.invoke(messages)
    print("model response >>>", ai_msg.content)
    return ai_msg.content


def create_agent(prompt, tools=[]):
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.7,
        max_tokens=None,
        timeout=None,
        max_retries=2,
        safety_settings={
            HarmCategory.HARM_CATEGORY_SEXUAL: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_UNSPECIFIED: HarmBlockThreshold.BLOCK_NONE,
        },
        # other params...
    )
    llm_with_tools = llm.bind_tools(tools)
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                prompt,
            ),
            ("human", "{input}"),
        ]
    )

    chain = prompt | llm_with_tools
    return chain


def main():
    # Define a simple prompt for the agent
    prompt = """
    You are a dating AI assistant That decides whether to like or dislike a potential match.
    The following tools are available to you:
    """ + "\n".join([f"- {tool.name}: {tool.description}" for tool in get_tools()])
    prompt += """
    Your goal is to decide whether to like or dislike a potential match based on the information provided.
    Use all of the tools at your disposal to make an informed decision.
    When you have enough information, respond with either "like" or "dislike".
    """
    query = "create a file named test.txt with a dirty pickup line, written in hebrew"
    chain = create_agent(prompt=prompt, tools=get_dating_tools())
    run_agent(chain, query)


if __name__ == "__main__":
    main()