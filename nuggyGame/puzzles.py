import random

MAX_LEVEL = 5
PUZZLES_PER_LEVEL = 10

class Puzzle:
    """
    Represents a puzzle with a description, solution, solved state, and optional hint.
    """
    def __init__(self, description, solution):
        self.description = description
        self.solution = solution
        self.solved = False

    def check_solution(self, answer):
        """Return True if the provided answer matches the solution."""
        return answer.strip().lower() == self.solution.lower()

    def get_hint(self):
        """Return a basic hint by revealing the first character of the solution."""
        if self.solution:
            return f"Hint: The answer starts with '{self.solution[0].upper()}'."
        return "No hint available."

def create_puzzles(level=1, puzzles_per_level=PUZZLES_PER_LEVEL):
    """
    Create and return a list of puzzles for a given level.
    Shuffle them to randomize order, then slice to puzzles_per_level.
    """
    all_puzzles = {
        1: [
            Puzzle("What color is the sky on a clear day?", "blue"),
            Puzzle("What do you call a baby cat?", "kitten"),
            Puzzle("What is 2 + 2?", "4"),
            Puzzle("What is the opposite of cold?", "hot"),
            Puzzle("What do bees produce?", "honey"),
            Puzzle("What is the capital of France?", "paris"),
            Puzzle("What is the largest planet in our solar system?", "jupiter"),
            Puzzle("What language do they speak in Spain?", "spanish"),
            Puzzle("What is H2O commonly known as?", "water"),
            Puzzle("What tool do you use to drive a nail?", "hammer"),
        ],
        2: [
            Puzzle("What is the capital of Italy?", "rome"),
            Puzzle("What is the color of grass?", "green"),
            Puzzle("What is the largest mammal?", "blue whale"),
            Puzzle("What planet do we live on?", "earth"),
            Puzzle("What fruit do hamsters love? (a type)", "apple"),
            Puzzle("What is the tallest mountain in the world?", "everest"),
            Puzzle("What year did the first man land on the moon?", "1969"),
            Puzzle("What is the chemical symbol for water?", "h2o"),
            Puzzle("Who wrote 'Romeo and Juliet'?", "shakespeare"),
            Puzzle("What is the boiling point of water in Celsius?", "100"),
        ],
        3: [
            Puzzle("What gas do plants absorb from the atmosphere?", "carbon dioxide"),
            Puzzle("What is the smallest prime number?", "2"),
            Puzzle("In which continent is the Sahara Desert located?", "africa"),
            Puzzle("What is the hardest natural substance?", "diamond"),
            Puzzle("What is the longest river in the world?", "nile"),
            Puzzle("Who painted the Mona Lisa?", "da vinci"),
            Puzzle("What is the powerhouse of the cell?", "mitochondria"),
            Puzzle("What is the speed of light in vacuum in km/s?", "299792"),
            Puzzle("What language has the most native speakers?", "chinese"),
            Puzzle("What is H2O commonly known as?", "water"),
        ],
        4: [
            Puzzle("What is the capital of Japan?", "tokyo"),
            Puzzle("What is the largest ocean on Earth?", "pacific"),
            Puzzle("What is the process by which plants make their food?", "photosynthesis"),
            Puzzle("What is the smallest continent?", "australia"),
            Puzzle("What is the closest star to Earth?", "sun"),
            Puzzle("What is the largest desert in the world?", "antarctica"),
            Puzzle("Who developed the theory of relativity?", "einstein"),
            Puzzle("What is the capital of Canada?", "ottawa"),
            Puzzle("What element does 'O' represent on the periodic table?", "oxygen"),
            Puzzle("What is the hardest natural substance?", "diamond"),
        ],
        5: [
            Puzzle("What is the largest desert in the world?", "antarctica"),
            Puzzle("Who developed the theory of relativity?", "einstein"),
            Puzzle("What is the capital of Canada?", "ottawa"),
            Puzzle("What element does 'O' represent on the periodic table?", "oxygen"),
            Puzzle("What is the largest ocean on Earth?", "pacific"),
            Puzzle("What is the powerhouse of the cell?", "mitochondria"),
            Puzzle("What is the speed of light in vacuum in km/s?", "299792"),
            Puzzle("What language has the most native speakers?", "chinese"),
            Puzzle("What is the longest river in the world?", "nile"),
            Puzzle("What is the chemical symbol for water?", "h2o"),
        ],
    }
    selected = all_puzzles.get(level, [])
    unique = []
    seen = set()
    for p in selected:
        # Avoid duplicating puzzle descriptions
        if p.description.lower() not in seen:
            unique.append(p)
            seen.add(p.description.lower())
        if len(unique) >= puzzles_per_level:
            break
    random.shuffle(unique)
    return unique

def retrieve_random_puzzle(puzzles):
    """
    Return a random unsolved puzzle, or None if all puzzles are solved.
    """
    unsolved = [p for p in puzzles if not p.solved]
    if unsolved:
        return random.choice(unsolved)
    return None

def main():
    """Main function to run the puzzle game with levels."""
    print("Welcome to the Puzzle Game!")
    level = 1
    puzzles_per_level = PUZZLES_PER_LEVEL
    total_levels = MAX_LEVEL

    while level <= total_levels:
        print(f"\nStarting Level {level}")
        puzzles = create_puzzles(level, puzzles_per_level)
        while True:
            puzzle = retrieve_random_puzzle(puzzles)
            if puzzle is None:
                print(f"Level {level} completed!")
                break
            print(puzzle.description)
            while True:
                answer = input("Your answer (or type 'hint'): ")
                if answer.lower() == 'hint':
                    print(puzzle.get_hint())
                    continue
                if puzzle.check_solution(answer):
                    print("Correct!")
                    puzzle.solved = True
                    break
                else:
                    print("Incorrect! Try again.")
        level += 1

    print("\nCongratulations! You have completed all levels!")

if __name__ == "__main__":
    main()
