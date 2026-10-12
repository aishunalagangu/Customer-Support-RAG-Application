import ollama

MODEL_NAME = "llama3.2"


def generate_answer(question, context):

    prompt = f"""
You are a professional laptop customer support assistant.

Answer the customer's question using ONLY the support context below.

IMPORTANT:
Your response MUST be structured and easy to read.

Follow these rules:

1. Start with a short title using Markdown heading:
   ## Title

2. Give a short explanation in one or two sentences.

3. If there are multiple actions, use a numbered list:
   1. First action
   2. Second action
   3. Third action

4. Use bullet points for additional information:
   - Point one
   - Point two

5. Use **bold text** for important actions.

6. Do not write the entire answer as one paragraph.

7. Keep the answer concise and professional.

8. Do not invent information that is not present in the support context.

If the answer cannot be found in the support context, respond exactly:

I don't have enough information in the support documents to answer that.

Support Context:
{context}

Customer Question:
{question}

Return ONLY the final customer-support answer.
"""

    response = ollama.chat(
        model=MODEL_NAME,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    answer = response["message"]["content"]

    print("\n========== AI RESPONSE ==========")
    print(answer)
    print("=================================\n")

    return answer