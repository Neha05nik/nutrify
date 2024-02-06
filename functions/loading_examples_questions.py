import random
import os

def random_questions(k_selected=4):
    """
    Function that randomly pick k_selected questions from the examples_questions.txt file
    Take k_selected, number of questions to return as argument
    """
    file_path = os.path.join(os.getcwd(), "assets", "examples_questions.txt")
    # We read the examples_questions from the file and store them in a list
    with open(file_path, "r", encoding="utf-8") as file:
        questions = file.readlines()

    # Remove newline characters and strip extra whitespaces
    questions = [sentence.strip() for sentence in questions]

    # We randomly choose four sentences
    selected_questions = random.sample(questions, k=k_selected)

    return selected_questions