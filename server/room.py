class Room:
    def __init__(self, client1, client2):
        self.questions, self.answers = self.generate_questions()
        self.indexs = {client1: 0, client2: 0}
        self.finished = False
    
    def generate_questions(self):
        return ["1 + 1", "2 + 2", "3 + 3"], [2, 4, 6]
    
    def verify_answer(self, client, attempt):
        if self.finished:
            return False
        
        index = self.indexs[client]
        answer = self.answers[index]
        correct = answer == attempt

        if correct:
            self.indexs[client] += 1
        
        return correct
