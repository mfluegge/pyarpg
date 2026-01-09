import pygame


class World:
    def __init__(self, screen, player_stats):
        self.max_width = screen.width
        self.max_height = screen.height
        self.players = pygame.sprite.GroupSingle()
        self.enemies = pygame.sprite.Group()
        
        self.active_player_skills = pygame.sprite.Group()
        self.active_enemy_skills = pygame.sprite.Group()
        self.active_player_ground_skills = pygame.sprite.Group()

        self.pickups_waiting = pygame.sprite.Group()
        self.pickups_collected = pygame.sprite.Group()

        self.player_stats = player_stats

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

    def get_pickups(self):
        return self.pickups

    def add_enemy(self, enemy):
        self.enemies.add(enemy)
    
    def add_player(self, player):
        self.players.add(player)
    
    def add_active_enemy_skill(self, skill):
        self.active_enemy_skills.add(skill)

    def add_active_player_skill(self, skill):
        self.active_player_skills.add(skill)

    def add_pickup(self, pickup):
        self.pickups_waiting.add(pickup)
    
    def add_active_player_ground_skill(self, skill):
        self.active_player_ground_skills.add(skill)

