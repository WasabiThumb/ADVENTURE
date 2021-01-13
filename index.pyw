import pygame, sys, os, json, threading, random, tempfile
from Levenshtein import distance as stringdist
from functools import cmp_to_key
pygame.init()
pygame.mixer.init()

size = w, h = (640, 480)
screen = pygame.display.set_mode(size)
pygame.display.set_caption("ADVENTURE")

sprites = {}
for f in os.listdir('./assets/images'):
    sprites[f.split('.')[0]] = pygame.image.load(os.path.join('./assets/images', f))

realms = {}
def loadRealms():
    for f in os.listdir('./realms'):
        realm = {}
        realm['id'] = f
        for x in os.listdir('./realms/' + f):
            if ('image' in x):
                realm['image'] = './realms/' + f + "/" + x
            elif ('densecap' in x):
                with open('./realms/' + f + "/" + x, 'r') as file:
                    realm['captions'] = json.loads(file.read())
            elif ('credits' in x):
                with open('./realms/' + f + "/" + x, 'r') as file:
                    realm['credits'] = json.loads(file.read())
            elif ('scape' in x):
                realm['soundscape'] = './realms/' + f + "/" + x
        realms[f] = realm

loader = threading.Thread(target=loadRealms)
loader.start()

pygame.display.set_icon(sprites['icon'])

hover = False
running = True
clicking = False
clickingLast = False
scene = -1
loadreferrer = 0
realmid = None
realmimage = None
realmboxes = []

def loadScene():
    pygame.mixer.music.stop()
    if (not loader.is_alive()): return loadreferrer
    loading = sprites['loading']
    sz = loading.get_size()
    ps = (round((w-sz[0])/2),round((h-sz[1])/2))
    screen.blit(loading, ps)
    return -1

def mainScene():
    start = sprites['start']
    sz = start.get_size()
    ps = (round((w-sz[0])/2),round((h-sz[1])/2))
    if (clicking):
        pos = pygame.mouse.get_pos()
        if (pos[0] > ps[0] and pos[1] > ps[1]):
            if (pos[0] < (ps[0] + sz[0]) and pos[1] < (ps[1] + sz[1])):
                global realmid
                realmid = random.choice(list(realms.items()))[0]
                return 1
    screen.blit(start, ps)
    return 0

def loadRealmImage():
    global realmimage
    protoim = pygame.image.load(realms[realmid]['image'])
    protosize = protoim.get_size()
    pw = protosize[0]
    ph = protosize[1]
    npw = w
    nph = round(ph*(npw/pw))
    if (nph > h):
        nph = h
        npw = round(pw*(nph/ph))
    frame = pygame.Surface((w, h), flags=pygame.SRCALPHA)
    frame.fill((0,0,0,0))
    leftadd = round((w-npw)/2)
    topadd = round((h-nph)/2)
    frame.blit(pygame.transform.smoothscale(protoim, (npw, nph)), (leftadd, topadd))
    realmimage = frame
    captions = realms[realmid]['captions']['output']['captions']
    caps = []
    for caption in captions:
        confidence = caption['confidence']
        if (confidence < 0.6): continue
        x1 = caption['bounding_box'][0]
        y1 = caption['bounding_box'][1]
        x2 = caption['bounding_box'][2]
        y2 = caption['bounding_box'][3]
        x1 = round(x1*(npw/pw))+leftadd
        x2 = round(x2*(npw/pw))+leftadd
        y1 = round(y1*(nph/ph))+topadd
        y2 = round(y2*(nph/ph))+topadd
        compsz = (x2-x1, y2-y1) 
        rect = pygame.Rect((x1, y1), (x2-x1, y2-y1))
        label = caption['caption']
        caps.append((rect, label, confidence, compsz[0]*compsz[1]))
    global realmboxes
    realmboxes = caps
    pygame.mixer.music.load(realms[realmid]['soundscape'])

def realmScene():
    global realmimage
    if (realmimage == None):
        global loader
        loader = threading.Thread(target=loadRealmImage)
        loader.start()
        global loadreferrer
        loadreferrer = 1
        return -1
    pos = pygame.mouse.get_pos()
    if (not pygame.mixer.music.get_busy()):
        pygame.mixer.music.play()
    isHover = False;
    hovers = [];
    global realmboxes
    for box in realmboxes:
        if box[0].collidepoint(pos):
            isHover = True
            hovers.append(box)
    global hover
    hover = isHover
    global clicking
    if (clicking):
        smallestBox = None
        smallest = w*h*2
        for box in hovers:
            if (box[3] < smallest):
                smallest = box[3]
                smallestBox = box
        if (smallestBox != None):
            term = smallestBox[1]
            terms = []
            global realms
            global realmid
            for rl in realms.items():
                if (rl[1]['id'] == realmid): continue
                for cap in rl[1]['captions']['output']['captions']:
                    tmt = {}
                    tmt['parent'] = rl[1]['id']
                    tmt['term'] = cap['caption']
                    tmt['confidence'] = cap['confidence']
                    terms.append(tmt)
            if (len(terms) > 0):
                def compareTerms(a, b):
                    distA = stringdist(a['term'],term)
                    distB = stringdist(b['term'],term)
                    if distA < distB:
                        return -1
                    elif distA > distB:
                        return 1
                    else:
                        confA = a['confidence']
                        confB = b['confidence']
                        if confA < confB:
                            return -1
                        elif confA > confB:
                            return 1
                        else:
                            return 0
                terms = sorted(terms, key=cmp_to_key(compareTerms))
                selected = terms[0]
                realmid = selected['parent']
                realmimage = None
                return 1
    screen.blit(realmimage, (0,0))
    return 1

scenemap = {-1: loadScene, 0: mainScene, 1: realmScene}

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            sys.exit(0)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                pygame.quit()
    if (not running): break
    #
    prss = pygame.mouse.get_pressed()[0]
    if (prss):
        if (clickingLast):
            clicking = False
        else:
            clicking = True
    else:
        clicking = False
    clickingLast = prss
    #
    screen.fill((0, 128, 128))
    #
    scene = scenemap[scene]()
    #
    pos = pygame.mouse.get_pos()
    if (pygame.mouse.get_focused()):
        pygame.mouse.set_visible(False)
        screen.blit(sprites['pointer' if not hover else 'hand'], (pos[0] - (0 if not hover else 5), pos[1]))
    pygame.display.flip()
