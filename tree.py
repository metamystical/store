import pyautogui as pg
import pyperclip as pc
from pynput.mouse import Controller; mouse = Controller()
import re
import time
import sqlite3
import os
import sys

contract = (21, 62)
center = ('', 681, 550)
    
sectors = [
    ('F', 624, 510),
    ('FF', 574, 539),
    ('FFF', 508, 562),
    ('FFFF', 422, 599),
    ('FFFM', 419, 541),
    ('FFM', 521, 486),
    ('FFMF', 429, 479),
    ('FFMM', 454, 421),
    ('FM', 630, 455),
    ('FMF', 568, 422),
    ('FMFF', 488, 373),
    ('FMFM', 539, 334),
    ('FMM', 642, 385),
    ('FMMF', 589, 306),
    ('FMMM', 649, 296),
    ('M', 735, 511),
    ('MF', 730, 455),
    ('MFF', 721, 385),
    ('MFFF', 710, 303),
    ('MFFM', 772, 312),
    ('MFM', 793, 421),
    ('MFMF', 830, 335),
    ('MFMM', 871, 377),
    ('MM', 789, 533),
    ('MMF', 841, 484),
    ('MMFF', 912, 422),
    ('MMFM', 932, 475),
    ('MMM', 851, 563),
    ('MMMF', 942, 538),
    ('MMMM', 938, 599),  
]

expand = [
    ('FFFF', 464, 596),
    ('FFFM', 459, 544),
    ('FFMF', 468, 492),
    ('FFMM', 488, 444),
    ('FMFF', 519, 401),
    ('FMFM', 558, 366),
    ('FMMF', 606, 344),
    ('FMMM', 657, 331),
    ('MFFF', 709, 330),
    ('MFFM', 761, 343),
    ('MFMF', 807, 369),
    ('MFMM', 845, 399),
    ('MMFF', 879, 444),
    ('MMFM', 899, 494),
    ('MMMF', 907, 545),
    ('MMMM', 903, 598)
]

pattern = re.compile('^[A-Z1-9]{4}-[A-Z1-9]{3}$') # for code

found = False
for window in pg.getAllWindows():
    if re.search('^Home • FamilySearch.*', window.title):
        found = True
        window.activate()
        time.sleep(1)
        break
if not found: sys.exit()

db = 'tree.db'
is_db = False
if os.path.isfile(db): is_db = True
connection = sqlite3.connect('tree.db')
cursor = connection.cursor()
if is_db: print('Existing db opened')
else:
    cursor.execute('create table tree (id integer primary key autoincrement, chain text not null unique, code varchar(8) not null, name text, birth_date text, birth_place text, death_date text, death_place text)')
    print ('New db created')
#sys.exit()

def crash(mess):
    print(mess); sys.exit()
    
def insert(tup):
    def insertcc(cc):
        try: cursor.execute('insert into chains (chain, code) values (?, ?)', cc)
        except sqlite3.IntegrityError as e: print(f'Chain already exists: {cc[0]}')
        
    chain = tup[0:1][0]
    code = tup[1:2][0]
    result = cursor.execute('select code from tree where code = ?', (code,)).fetchone()
    if result == None:
        #print('ancestor does not exist, adding', code, chain)
        cursor.execute('insert into tree (code, name, birth_date, birth_place, death_date, death_place) values (?, ?, ?, ?, ?, ?)', tup[1:])
        insertcc(tup[:2])
        connection.commit()
        return([])
    # ancestor already existed; add every ancestor further up the tree
    #print('ancestor existed', code, chain)
    bases = cursor.execute("select chain from chains where code = ?", (code,)).fetchall()
    ccss = []
    for bs in bases:
        ccs = cursor.execute("select chain, code from chains where chain like ?", (f'{bs[0]}%',)).fetchall()
        ccs = [(cs[0][len(bs[0]):], cs[1]) for cs in ccs] # strip base
        ccss += ccs
    ccss = list(set(ccss)) # removes duplicates
    ret = []
    for ccs in ccss:
        if ccs[1] == code: continue
        ch = chain + ccs[0]
        # print('adding:', *ccs, ch)
        insertcc((ch, ccs[1]))
        ret.append(ch)
    connection.commit()
    return(ret)

def get_code(chain): # returns code string or empty string if no code found
    code = cursor.execute("select code from chains where chain = '" + chain + "'").fetchone()
    if code == None: return ''
    return code[0]

def get_counts():
    def get_count(table):
        return(cursor.execute(f'select count(*) from {table}').fetchone()[0])
    print('#ancestors:', get_count('tree'), get_count('chains'))

def grab(x, y, nofollow): # get the details of an ancestor at x,y; return tuple, could be ()
    pc.copy('xyzzy')
    pg.click(x, y); time.sleep(0.4) # open detail popup
    pg.hotkey('ctrl', 'a'); pg.hotkey('ctrl', 'c') # select all, copy
    if(pc.paste() == 'xyzzy'): return(())
    lines = pc.paste().splitlines()
    offset = 2
    def refresh():
        time.sleep(0.4)
        pg.hotkey('ctrl', 'a'); pg.hotkey('ctrl', 'c')
        lines = pc.paste().splitlines()
    def get_line(index):
        for round in range(4): # three tries
            if round == 3: crash('line not found')
            try: line = lines[index]
            except Exception as e:
                refresh()
                continue
            break
        return(line)
    code = ''
    for round in range(4): # three tries
        if round == 3: return(())
        code1 = get_line(offset + 24)[:-2]
        m1 = bool(pattern.match(code1))
        code2 = get_line(offset + 25)[:-2]
        m2 = bool(pattern.match(code2))
        if not m1 and not m2:
            refresh()
            continue
        if m2: # profile has a picture
             offset += 1
             code = code2
        else: code = code1
        break
    name = get_line(offset + 23)
    if nofollow: offset -= 1
    pg.press('esc'); time.sleep(0.4) # close detail popup
    f = []
    f.append(get_line(offset + 26))
    f.append(get_line(offset + 27))
    f.append(get_line(offset + 28))
    f.append(get_line(offset + 29))
    f.append(get_line(offset + 30))
    f.append(get_line(offset + 31))
    f.append(get_line(offset + 32))
    f.append(get_line(offset + 33))
    # find markers
    birth = -1; death = -1; sources = -1
    for i in range(0, len(f)):
        if f[i] == 'Birth' or f[i] == 'Christening': birth = i
        if f[i] == 'Death' or f[i] == 'Burial': death = i
        if f[i] == 'Sources':
            if not bool(re.match(r'^\d+$', f[i - 1])): crash('sources anomoly')
            sources = i - 1
    if birth == -1: crash('birth anomoly')
    if death == -1: crash('death anomoly')
    if sources == -1: crash('sources anomoly')
    def has_digit(date):
        return bool(re.search(r'\d', date)) or date == 'Living' or date == 'Deceased'
    def get_pair(start, end):
        date = ''; place = ''
        s1 = start + 1; s2 = start + 2
        if end > s1:
            a = f[s1]
            if has_digit(a) or a == 'unknown' or a == 'Sep' or a == 'date not given':
                date = a
                if end > s2: place = f[s2]
            else:
                if end > s2 or has_digit(a) or a == 'unknown' or a == 'Sep' or a == 'date not given': crash('date anomoly')
                place = a
        return((date, place))
    birth_date, birth_place = get_pair(birth, death)
    death_date, death_place = get_pair(death, sources)
    return((code, name, birth_date, birth_place, death_date, death_place))

def gray(x, y):
    color = pg.pixel(x, y) # returns RGB triplet
    if color == (242, 242, 242) or color == (232, 232, 232) or color == (216, 216, 216): return(True)
    return(False)
    
def fan(origin): # insert the details of every ancestor in the fan into the db
    skip = []
    for ch, x, y in sectors:
        chain = origin + ch
        if chain in skip: continue
        color = pg.pixel(x, y) # returns RGB triplet
        if gray(x, y): continue
        tup = grab(x, y, False)
        if len(tup) > 0: skip = insert((chain,) + tup)
    get_counts()

def grab_center(code): # crash upon fail
    for round in range(4): # three tries
        if round == 3: crash('fan not loaded')
        time.sleep(1)
        offset = -10 + 10 * round # in case of no last name
        ch, x, y = center # go to center
        tup = grab(x, y + offset, code == '')
        if len(tup) == 0: continue
        if (code == '' or code == tup[0]): return(tup)
        print(f'code mismatch {code} vs {tup[0]} at {tup[1]}')
        return(tup)

if not is_db: # grab and insert home
    tup = grab_center('')
    insert(('',) + tup)
    fan('')

start = 80
step = 10
with open('level5.csv', 'r') as file: lines = file.readlines()
print("Leve5", len(lines))
level5 = [line.rstrip('\n') for line in lines[start:start + step]]
print(f"Level5: {start} to {start + step - 1} inclusive")
for i in range(0, step):
    base = level5[i]
    if len(base) % 4 != 0 or not bool(re.match(r'[FM]*$', base)): crash('bad base')
    # load base fan
    base_code = get_code(base)
    print(i, base, base_code)
    if len(base_code) != 8: crash('db error')
    pg.click(206, 62); time.sleep(0.2)
    pc.copy('https://www.familysearch.org/tree/pedigree/fanchart/' + base_code)
    pg.hotkey('ctrl', 'v'); time.sleep(0.2) # paste
    pg.press('enter'); time.sleep(2)
    grab_center(base_code) # confirm
    fan(base) # grab base fan
    for target in expand:
        # load target fan one level up
        new_base = base + target[0]
        new_code = get_code(new_base)
        #print('new', new_code, new_base)
        if len(new_code) != 8: continue
        ch, x, y = [tup for tup in expand if tup[0] == new_base[-4:]][0]
        # test for missing sector
        if gray(x, y):
            print(f'{new_code} is no longer an ancestor at {new_base}')
            continue
        pg.click(x, y); time.sleep(2) # load new fan
        grab_center(new_code)
        fan(new_base)
        x, y = contract # return to base via back arrow
        pg.click(x, y)
        #print('mark', new_base, new_code, base_code)
        grab_center(base_code) 

cursor.close()
connection.close()
