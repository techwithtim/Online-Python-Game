import pygame
from client import Client
from protocols import Protocols

class MathGame:
    def __init__(self, client):
        self.client = client 
        client.start()

        self.font = None
        self.input_box = pygame.Rect(100, 100, 400, 45)
        self.color_inactive = pygame.Color("lightskyblue3")
        self.color_active = pygame.Color("dodgerblue2")
        self.color = self.color_inactive

        self.text = ""
        self.done = False
        self.logged_in = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.input_box.collidepoint(event.pos):
                self.color = self.color_active
            else:
                self.color = self.color_inactive
        
        if event.type != pygame.KEYDOWN or self.color == self.color_inactive:
            return
        
        if event.key == pygame.K_RETURN:
            if not self.logged_in:
                self.client.send(Protocols.Request.NICKNAME, self.text)
                self.client.nickname = self.text
                self.logged_in = True
                self.text = ""
            elif self.client.started:
                self.client.send(Protocols.Request.ANSWER, int(self.text))
                self.client.client_validate_answer(self.text)
                self.text = ""
        elif event.key == pygame.K_BACKSPACE:
            self.text = self.text[:-1]
        else:
            self.text += event.unicode

    def draw(self, screen):
        screen.fill((255, 255, 255))
        if not self.logged_in and not self.client.started:
            self.draw_login(screen)
        elif not self.client.started:
            self.draw_waiting(screen)
        else:
            self.draw_game(screen)
        
        pygame.display.update()

    def draw_waiting(self, screen):
        text = 'Waiting for player'
        text_surface = self.font.render(text, 1, (0, 0, 0))
        screen.blit(text_surface, (screen.get_width()/2 - text_surface.get_width()/2, screen.get_height()/2 - text_surface.get_height()/2))
    
    def draw_login(self, screen):
        prompt = 'Enter A Nickname'
        prompt_surface = self.font.render(prompt, 1, (0, 0, 0))
        screen.blit(prompt_surface, (100, 50))
        self.draw_input(screen)

    def draw_input(self, screen):
        pygame.draw.rect(screen, self.color, self.input_box, 2)
        txt_surface = self.font.render(self.text, 1, self.color)
        screen.blit(txt_surface, (self.input_box.x + 5, self.input_box.y + 5))
        self.input_box.w = max(100, txt_surface.get_width()+10)
    
    def draw_game(self, screen):
        question = self.client.get_current_question()
        question_surface = self.font.render(f"#{self.client.current_question_index + 1}: {question} = ", 1, (0, 0, 0))
        screen.blit(question_surface, (100, 50))
        self.draw_input(screen)
        self.draw_opponent_data(screen)

    def draw_opponent_data(self, screen):
        if not self.client.opponent_data:
            return

        name_surface = self.font.render(f"Opponent: {self.client.opponent_data['name']}", 1, (0, 0, 0))
        screen.blit(name_surface, (550, 50))

        wins_surface = self.font.render(f"Wins: {self.client.opponent_data['wins']}", 1, (0, 0, 0))
        screen.blit(wins_surface, (550, 100))

        loss_surface = self.font.render(f"Losses: {self.client.opponent_data['losses']}", 1, (0, 0, 0))
        screen.blit(loss_surface, (550, 150))

        question_num = self.client.opponent_question_index + 1
        question_surface = self.font.render(f"Question #{question_num}", 1, (0,0,0))
        screen.blit(question_surface, (550, 200))
    
    def handle_end(self, screen):
        run = True
        while run:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False
            
            if self.client.winner:
                text = f"{self.client.winner} has won the game!"
            else:
                text = f"Opponent left the game..."
            
            text_surface = self.font.render(text, 1, (0, 0, 0))
            screen.blit(text_surface,(screen.get_width()/2 - text_surface.get_width()/2, screen.get_height()/2 - text_surface.get_height()/2))
            pygame.display.update()

    def run(self):
        pygame.init()
        screen = pygame.display.set_mode((800, 600))
        clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("comicsans", 32)

        while not self.client.closed:
            clock.tick(30)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.client.close()
                    pygame.quit()
                else:
                    self.handle_event(event)
            
            self.draw(screen)
        
        self.handle_end(screen)
        pygame.quit()

if __name__ == "__main__":
    game = MathGame(Client())
    game.run()