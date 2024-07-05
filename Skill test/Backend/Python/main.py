from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import google.generativeai as genai
from fastapi.middleware.cors import CORSMiddleware

# Configure the API key
genai.configure(api_key="AIzaSyAFo-zdP8RfCi8XbNSUx1lYSD_H_K5gwmM")

# Create FastAPI instance
app = FastAPI()

score = 0

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],             # List of allowed origins
    allow_credentials=True,            # Allow cookies and authentication headers
    allow_methods=["*"],               # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],               # Allow all headers
)

# Define request models
class QuestionRequest(BaseModel):
    topic: str
    difficulty: str
    num_questions: int

class AnswerRequest(BaseModel):
    index: int
    answer: str

# Define response models
class QuestionResponse(BaseModel):
    index: int
    question: str

class EvaluationResponse(BaseModel):
    score: float
    perfect_answer: str

# Create the model
generation_config = {
    "temperature": 0.9,
    "top_p": 1,
    "top_k": 0,
    "max_output_tokens": 2048,
    "response_mime_type": "text/plain",
}
safety_settings = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE",
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE",
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE",
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE",
    },
]
model = genai.GenerativeModel(
    model_name="gemini-1.0-pro",
    safety_settings=safety_settings,
    generation_config=generation_config,
)

# Store generated questions in memory (for simplicity)
generated_questions = []

# Define API endpoint to generate questions
@app.post("/generate_questions", response_model=list[QuestionResponse])
async def generate_questions(request: QuestionRequest):
    global score
    score = 0
    prompt = f"Generate {request.num_questions} questions on the topic '{request.topic}' with a difficulty level of '{request.difficulty}'."
    chat_session = model.start_chat()
    response = chat_session.send_message(prompt)
    questions = response.text.split("\n")
    
    # Clear the old questions
    global generated_questions
    generated_questions = []

    # Create a list of questions with index numbers, only if they start with a number
    indexed_questions = [{"index": i + 1, "question": question} for i, question in enumerate(questions) if question and question[0].isdigit()]
    
    # Store the questions in memory
    generated_questions.extend(indexed_questions)

    return generated_questions

# Define API endpoint to evaluate answers
@app.post("/evaluate_answer", response_model=EvaluationResponse)
async def evaluate_answer(request: AnswerRequest):
    # Check if the question index exists
    if request.index < 0 or request.index > len(generated_questions):
        print(request.index)
        raise HTTPException(status_code=403, detail="Question index out of range")

    # Retrieve the question based on index
    question = generated_questions[request.index - 1]["question"]

    # Create a prompt for evaluation
    evaluation_prompt = f"Evaluate the following answer to the question: '{question}'\n\nAnswer: {request.answer}\n\nPlease provide a score out of 10 and the perfect answer. The score should be in the format 'Score: X' where X is a number between 0 and 10. Use just plain text. Do not use any bold text or any other styling to the fonts"

    # Get evaluation response from the model
    evaluation_response = model.start_chat(
        history=[
            {
                "role": "user",
                "parts": [
                    "Hi",
                ],
            },
            {
                "role": "model",
                "parts": [
                    "Hi there! How can I assist you today?",
                ],
            },
        ]
    ).send_message(evaluation_prompt)

    # Print the raw response for debugging
    print("Raw evaluation response:", evaluation_response.text)

    # Parse the evaluation response
    evaluation_lines = evaluation_response.text.split("\n")
    score_line = next((line for line in evaluation_lines if "Score: " in line), "Score: 0")
    perfect_answer_lines = evaluation_lines[evaluation_lines.index(score_line) + 1:]
    print(score_line+"This is the score line")

    try:
        global score 
        score += float(score_line.split("Score: ")[1].strip())
        print(score,"This is the score")
    except (IndexError, ValueError):
        print("Error")
        score = 0.0

    perfect_answer = "\n".join(perfect_answer_lines).strip()
    print("Score is", score)

    return EvaluationResponse(score=score, perfect_answer=perfect_answer)


@app.get("/generated_questions", response_model=list[QuestionResponse])
async def get_generated_questions():
    return generated_questions


@app.get("/get-score")
async def get_Score():
    global score
    return score

# Run the FastAPI application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


