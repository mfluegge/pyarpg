import pygame


class World:
    def __init__(self, screen):
        self.max_width = screen.width
        self.max_height = screen.height
        self.players = pygame.sprite.GroupSingle()
        self.enemies = pygame.sprite.Group()
        
        self.active_player_skills = pygame.sprite.Group()
        self.active_enemy_skills = pygame.sprite.Group()

    @property
    def player(self):
        return self.players.sprite

    def get_enemies(self):
        return self.enemies

    def get_player(self):
        return self.player
    
    def get_player_group(self):
        return self.players

    def get_active_enemy_skills(self):
        return self.active_enemy_skills

    def get_active_player_skills(self):
        return self.active_player_skills

    def add_enemy(self, enemy):
        self.enemies.add(enemy)
    
    def add_player(self, player):
        self.players.add(player)
    
    def add_active_enemy_skill(self, skill):
        self.active_enemy_skills.add(skill)

    def add_active_player_skill(self, skill):
        self.active_player_skills.add(skill)