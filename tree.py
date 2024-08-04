import pyautogui as pg
import pyperclip as pc
import re
import time
import sys
import utils

def crash(mess):
    print(mess); utils.close_db(); sys.exit()

def grab(x, y, nofollow): # get the details of an ancestor at x,y; return tuple, could be ()
    def get_line(index): # statics got_lines and lines are lost when grab() returns
        if not hasattr(get_line, "got_lines"): get_line.got_lines = False
        if not get_line.got_lines:
            pg.hotkey('ctrl', 'a'); pg.hotkey('ctrl', 'c') # select all, copy
            get_line.lines = pc.paste().splitlines()
        try: line = get_line.lines[index]
        except Exception as e: crash('line not found at index ' + str(index))
        return(line)
    for round in range(4): # three tries waiting for detail to appear and be copied
        if round == 3:
            pg.press('esc'); time.sleep(0.1) # close detail
            return(())
        pc.copy('xyzzy')
        pg.click(x, y); time.sleep(0.4) # open detail popup
        pg.hotkey('ctrl', 'a'); pg.hotkey('ctrl', 'c') # select all, copy
        if pc.paste() != 'xyzzy': break
    offset = 2
    code = ''
    pattern = re.compile('^[A-Z1-9]{4}-[A-Z1-9]{3}$') # for code
    for round in range(4): # three tries waiting for delayed follow link
        if round == 3:
            pg.press('esc'); time.sleep(0.1) # close detail
            return(())
        code1 = get_line(offset + 24)[:-2]
        m1 = bool(pattern.match(code1))
        code2 = get_line(offset + 25)[:-2]
        m2 = bool(pattern.match(code2))
        if not m1 and not m2:
            time.sleep(0.4)
            continue
        if m2: # profile has a picture
             offset += 1
             code = code2
        else: code = code1
        break
    pg.press('esc'); time.sleep(0.1) # close detail
    get_line.got_lines = True
    name = get_line(offset + 23)
    if name.capitalize() == 'Unknown': return(())
    if nofollow: offset -= 1
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
        return bool(re.search(r'\d', date)) or date.capitalize() == 'Living' or date.capitalize() == 'Deceased'
    def get_pair(start, end):
        date = ''; place = ''
        s1 = start + 1; s2 = start + 2
        def anomolies(a):
            return(a.capitalize() == 'Unknown' or a.capitalize() == 'Sep' or a == '?' or a == 'date not given')
        if end > s1:
            a = f[s1]
            if has_digit(a) or anomolies(a):
                date = a
                if end > s2: place = f[s2]
            else:
                if end > s2 or anomolies(a): crash('date anomoly:' + a)
                place = a
        return((date, place))
    birth_date, birth_place = get_pair(birth, death)
    death_date, death_place = get_pair(death, sources)
    return((code, name, birth_date, birth_place, death_date, death_place))

def grab_center(code): # crash upon fail
    for round in range(4): # three tries moving slightly in center to get to link
        if round == 3: crash('fan not loaded')
        offset = -4 + 8 * round # in case of no last name
        ch, x, y = center # go to center
        tup = grab(x, y + offset, code == '')
        if len(tup) == 0:
            time.sleep(0.4)
            continue
        if (code == '' or code == tup[0]): return(tup)
        crash(f'code mismatch {code} vs {tup[0]} at {tup[1]}')
        return(tup)

def gray(x, y):
    color = pg.pixel(x, y) # returns RGB triplet
    if color == (242, 242, 242) or color == (232, 232, 232) or color == (216, 216, 216): return(True)
    return(False)

def insert(tup):
    chain = tup[0:1][0]
    code = tup[1:2][0]
    if not utils.is_code(code):
        utils.insert_tree(tup[1:])
        utils.insert_chains(tup[:2])
        utils.commit()
        return([])
    # ancestor already existed; add every ancestor further up the tree
    #print('ancestor existed', code, chain)
    bases = utils.get_chains(code)
    #print('bases', bases)
    ccss = []
    for bs in bases:
        ccs = utils.get_ccs_with_base(bs)
        ccs = [(cs[0][len(bs):], cs[1]) for cs in ccs] # strip base
        ccss += ccs
    ccss = list(set(ccss)) # removes duplicates
    #print('ccss', ccss)
    ret = []
    for ccs in ccss:
        ch = chain + ccs[0]
        #print('adding:', *ccs, ch)
        utils.insert_chains((ch, ccs[1]))
        ret.append(ch)
    utils.commit()
    return(ret)

def fan(origin): # insert the details of every ancestor in the fan into the db
    skip = []
    for ch, x, y in sectors:
        chain = origin + ch
        if chain in skip: continue
        color = pg.pixel(x, y) # returns RGB triplet
        if gray(x, y): continue
        tup = grab(x, y, False)
        if len(tup) > 0: skip += insert((chain,) + tup)
    print('#ancestors:', utils.get_count('tree'), utils.get_count('chains'))

#title = 'Home • FamilySearch'
title = 'Dr. John'
utils.activate('^' + title + '.*')
sectors = utils.fan()
center = sectors.pop(0)
is_db = utils.open_db('tree.db')

if not is_db: # grab and insert home fan
    utils.setup()
    tup = grab_center('')
    insert(('',) + tup)
    fan('')

generation = 12 # multiples of 6, not including me #433
gen = utils.get_gen(generation)
print(f"Generation {generation}: {len(gen)} ancestors")
start = 433 # start at 0
step = 1 # add this to start when ready for next run
print(f"Gen {generation}: {start} to {start + step - 1} inclusive")
for i in range(start, start + step):
    base = gen[i]
    if len(base) % 6 != 0 or not bool(re.match(r'[FM]*$', base)): crash('bad base')
    base_code = utils.get_code(base)
    print(i, base, base_code)
    if len(base_code) != 8: crash('db error')
    pg.click(206, 62); time.sleep(0.2)
    pc.copy('https://www.familysearch.org/tree/pedigree/fanchart/' + base_code)
    pg.hotkey('ctrl', 'v'); time.sleep(0.2) # paste
    pg.press('enter'); time.sleep(4.6)
    utils.setup()
    grab_center(base_code) # confirm
    fan(base)
utils.close_db()
