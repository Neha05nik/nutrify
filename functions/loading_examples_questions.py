import random

def random_questions(k_selected=4):
    """
    Function that randomly pick k_selected questions from the examples_questions.txt file
    Take k_selected, number of questions to return as argument
    """

    # We read the examples_questions from the file and store them in a list
    with open("assets\examples_questions.txt", "r", encoding="utf-8") as file:
        questions = file.readlines()

    # Remove newline characters and strip extra whitespaces
    questions = [sentence.strip() for sentence in questions]

    # We randomly choose four sentences
    selected_questions = random.choices(questions, k=k_selected)

    return selected_questions