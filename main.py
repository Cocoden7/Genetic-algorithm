"""
Algorithme génétique qui fait en sorte que les particules suivent un chemin donné
"""

import pygame
import random
import time
import math
import matplotlib.pyplot as plt


pygame.font.init()


RESOLUTION = (600, 600)
WINDOW = pygame.display.set_mode(RESOLUTION, pygame.FULLSCREEN)
BLACK = (0, 0, 0)
GO = True
FPS = 60
CLOCK = pygame.time.Clock()
POPULATION_SIZE = 1000
NUMBER_OF_MOVES = 200
GRADED_RETAIN_PERCENT = 0.05 # 20%
NUMBER_OF_GRADED_RETAIN = int(POPULATION_SIZE * GRADED_RETAIN_PERCENT)
CHANCE_RETAIN_NON_GRADED = 0.1 # 0 < chance < 1
CHANCE_TO_MUTATE = 0.015
PERCENT_OF_MUTATION = 0.3
NUMBER_OF_MUTATIONS = int(PERCENT_OF_MUTATION * NUMBER_OF_MOVES)
PERCENT_OF_CROSSING_OVER = 0.5

MAX = 0

NUMBER_OF_GENERATIONS = 10

SIZE_TEXT = 30
POLICE = pygame.font.Font('vermin_vibes_1989.ttf', SIZE_TEXT)

SPEED_X = 5
SPEED_Y = 5
TAILLE = 5
PARTICLE_RECT = pygame.Rect(300, 300, TAILLE, TAILLE)


def random_color():
    return random.randint(0, 252), random.randint(0, 252), random.randint(0, 252)


def get_text_image(text):
    return POLICE.render(text, 1, (0, 252, 0))


def write_on_screen(text, position):
    WINDOW.blit(get_text_image(text), position)

"""
Class representing an individual
"""


class Particle:
    ID = 0

    def __init__(self,rect):
        Particle.ID += 1
        self.ID = Particle.ID
        self.fitness = 0
        self.color = random_color()
        self.rect = rect
        self.moves = [] * NUMBER_OF_MOVES
        self.distance_with_end = 1
        self.visibility = False

    def fitness_add(self):
        self.fitness += 1

    # Ajoute une vitesse random
    def generate_random_moves(self):
        for i in range(NUMBER_OF_MOVES):
            self.moves.append((random.randint(-SPEED_X, SPEED_X), random.randint(-SPEED_Y, SPEED_Y)))

    def collide(self, rect):
        return self.rect.colliderect(rect)

    def move(self, tiles, count):
        self.rect.x += self.moves[count][0]
        self.rect.y += self.moves[count][1]
        coll = False
        for tile in tiles:
            # récompense
            if self.collide(tile):
                coll = True
                self.fitness_add()

    def fitness_is_zero(self):
        return self.fitness == 0

"""
Class for creating the level
"""


class Level():
    def __init__(self, fichier):
        self.fichier = fichier
        self.tiles = []
        self.other_tiles = []
        self.start_pos = (0, 0)
        self.end_pos = (0, 0)

    def generate(self):
        fichier_texte = open(self.fichier, "r")
        contenu = fichier_texte.read()
        j = 0
        k = 0
        for i in contenu:
            if i == "\n":
                j += 1
                k = -1
            if i == '#':
                # tiles.append(pygame.Rect(k*50,j*50,50,50))
                self.tiles.append(pygame.Rect(k * 30, j * 30, 30, 30))
            if i == '*':
                self.start_pos = (k * 30, j * 30)
                self.other_tiles.append(pygame.Rect(k * 30, j * 30, 30, 30))
            if i == '+':
                self.end_pos = (k * 30, j * 30)
                self.other_tiles.append((pygame.Rect(k * 30, j* 30, 30, 30)))
            k += 1
        fichier_texte.close()

    def draw(self):
        for i in self.tiles:
            pygame.draw.rect(WINDOW, (252, 0, 0), i)
        for i in self.other_tiles:
            pygame.draw.rect(WINDOW, (0,252,0), i)

"""
Class who deals with the level and a generation
"""


class Game:
    def __init__(self, level):
        self.level = level
        self.population = []
        self.generation = 1
        self.generation_tab = []
        self.average_fitness_tab = []
        self.best_tab = []
        self.show_best = False

    def all_fitness_is_zero(self):
        for i in self.population:
            if i.fitness != 0:
                return False
        return True

    def generate_first_population(self):
        for i in range(POPULATION_SIZE):
            self.population.append(Particle(pygame.Rect(self.level.start_pos[0], self.level.start_pos[1], TAILLE, TAILLE)))
        for j in self.population:
            j.generate_random_moves()
        return self.population

    def set_visibility(self):
        for i in self.population:
            for tile in self.level.tiles:
                if i.collide(tile):
                    i.visibility = True

    def draw_particles(self):
        graded_population = self.get_graded_population()
        if not self.show_best:
            for i in self.population:
                pygame.draw.rect(WINDOW, i.color, i.rect)
        else:
            for i in graded_population[-10:]:
                pygame.draw.rect(WINDOW, (0, 0, 252), i[3])

    def move_particles(self, count):
        for i in self.population:
            i.move(self.level.tiles, count)

    def draw_window(self):
        WINDOW.fill(BLACK)
        self.level.draw()
        self.draw_particles()
        write_on_screen("Generation %s" % self.generation, (0, 0))
        pygame.display.update()

    # Class the population by croissant order of score
    def get_graded_population(self):
        graded_population = []
        for i in self.population:
            graded_population.append((i.ID, -i.distance_with_end + i.fitness, i.moves, i.rect)) #
        graded_population.sort(key=sort_second)
        return graded_population

    # Return the average fitness
    def get_average_fitness(self):
        average = 0.0
        for i in self.population:
            average += i.fitness
        return average / len(self.population)

    def generate_next_generation(self):
        actual_graded = self.get_graded_population()

        # Add the better ranked ones
        parents = actual_graded[-NUMBER_OF_GRADED_RETAIN:]

        # Add some low scored, for the diversity
        for individual in actual_graded[:(len(actual_graded)-NUMBER_OF_GRADED_RETAIN)]:
            if random.random() < CHANCE_RETAIN_NON_GRADED:
                parents.append(individual)

        # Mute individuals
        for individual in parents:
            if random.random() < CHANCE_TO_MUTATE:
                for i in range(NUMBER_OF_MUTATIONS):
                    individual[2][int(random.random()*len(individual[2]))] = (random.randint(-SPEED_X, SPEED_X),random.randint(-SPEED_Y, SPEED_Y))

        # Parents make childrens
        child_len = POPULATION_SIZE - len(parents)
        childs = []
        while len(childs) <= child_len:
            child = Particle(pygame.Rect(self.level.start_pos[0], self.level.start_pos[1], TAILLE, TAILLE))
            father = random.choice(parents)
            mother = random.choice(parents)
            # If father and mother are the same, we change
            while mother[0] == father[0]:
                mother = random.choice(parents)
            child.moves = [(0, 0)] * NUMBER_OF_MOVES
            for i in range(NUMBER_OF_MOVES):
                if random.random() < PERCENT_OF_CROSSING_OVER:
                    child.moves[i] = father[2][i]
                else:
                    child.moves[i] = mother[2][i]
            childs.append(child)
        parents.extend(childs)

        # We create a list (and not a tuple)
        new_generation = []
        for i in parents:
            if isinstance(i, tuple):
                child = Particle(pygame.Rect(self.level.start_pos[0], self.level.start_pos[1], TAILLE, TAILLE))
                child.moves = i[2]
                new_generation.append(child)
            else:
                new_generation.append(i)

        return new_generation

    def update(self):
        self.generation_tab.append(Game.generation)
        self.average_fitness_tab.append(Game.get_average_fitness())
        self.best_tab.append(Game.get_graded_population()[-1][1])
        self.generation += 1
        self.compute_distance()
        self.population = Game.generate_next_generation()

    def compute_distance(self):
        for i in self.population:
            i.distance_with_end = math.hypot(self.level.end_pos[0] - i.rect.x, self.level.end_pos[1] - i.rect.y)



level1 = Level("level1.txt")
Game = Game(level1)
Game.level.generate()
Game.generate_first_population()


def sort_second(val):
    return val[1]


def print_all():
    print("GENERATION %s \n" % Game.generation)
    for i in Game.get_graded_population():
        print("Particle ID %s : fitness = %s " % (i[0], i[1]))
    print("\n")
    print("NUMBER OF PARTICLES : %s"%len(Game.population))


# Generate some graphs
def graph():
    plt.grid(True)
    plt.subplot(2, 1, 1)
    plt.xlabel('Generation')
    plt.ylabel('Average fitness')
    plt.title('Generation versus average fitness')
    plt.plot(Game.generation_tab, Game.average_fitness_tab)
    plt.subplot(2, 1, 2)
    plt.xlabel('Generation')
    plt.ylabel('Best fitness')
    plt.title('Generation versus BF')
    plt.plot(Game.generation_tab, Game.best_tab)
    plt.show()


solution = 0
count = 0

time.sleep(5)
while GO:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            GO = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            Game.show_best = not Game.show_best
    Game.move_particles(count)
    Game.draw_window()
    count += 1
    if count == NUMBER_OF_MOVES-1:
        print_all()
        print("\n")
        count = 0
        Game.update()
    CLOCK.tick(FPS)



graph()
pygame.quit()
quit()
