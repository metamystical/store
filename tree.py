import pyautogui as pg
import pyperclip as pc
import re
import math
import time
import sys
import os
import sqlite3

def open_db(db): # statics conn and curs are preserved until calling function/program returns/exits
    is_db = False
    if os.path.isfile(db): is_db = True
    open_db.conn = sqlite3.connect('tree.db')
    open_db.curs = open_db.conn.cursor()
    if is_db: print('existing db opened')
    else:
        open_db.curs.execute('create table tree (id integer primary key autoincrement, code varchar(8) not null, name text, birth_date text, birth_place text, death_date text, death_place text)')
        open_db.curs.execute('create table chains (chain text not null unique, code varchar(8) not null)')
        open_db.curs.execute('create unique index inx_chain on chains (chain)')
        open_db.curs.execute('create index inx_code on chains (code)')
        print('new db created')
    return(is_db)

def close_db():
    open_db.curs.close()
    open_db.conn.close()
    print('db closed')

def commit():
    open_db.conn.commit()

def exec_ret(command, tup): # returns [] if no result, otherwise list of tuples
    return(open_db.curs.execute(command, tup).fetchall())

def exec(command, tup):
    try: open_db.curs.execute(command, tup)
    except Exception as e:
        #print(e)
        return(False)
    return(True)

def is_code(code):
    return(len(exec_ret('select code from tree where code = ?', (code,))) >= 1)

def insert_tree(tup):
    exec('insert into tree (code, name, birth_date, birth_place, death_date, death_place) values (?, ?, ?, ?, ?, ?)', tup)

def insert_chains(tup):
    exec('insert into chains (chain, code) values (?, ?)', tup)

def detuple_list(tups):
    if tups == None: return([])
    return([tup[0] for tup in tups])

def get_code(chain): # returns code string or empty string if no code found
    res = exec_ret('select code from chains where chain = ?', (chain,))
    res = detuple_list(res)
    if len(res) == 0: return ''
    return res[0]

def get_chains(code): # returns list of chain strings
    res = exec_ret("select chain from chains where code = ?", (code,))
    return(detuple_list(res))

def get_gen(generation): # returns list of chain strings
    res = exec_ret('select distinct chain from chains where length(chain) = ? order by chain', (generation,))
    return(detuple_list(res))

def get_ccs_with_base(base): # returns list of tuples
    res = exec_ret("select chain, code from chains where chain like ?", (f'{base}%',))
    if res == None: return([])
    return(res)

def get_count(table):
    return(exec_ret(f'select count(*) from {table}', ())[0][0])

def crash(mess):
    print(mess); close_db(); sys.exit()

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

def grab_center(center, code): # crash upon fail
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

def insert(chain, tup):
    code = tup[0]
    if not is_code(code):
        insert_tree(tup)
        insert_chains((chain, code))
        commit()
        return([])
    # ancestor already existed; add every ancestor further up the tree
    print('ancestor existed', code, chain)
    bases = get_chains(code)
    print('bases', bases)
    ccss = []
    max_ccs = 0
    for bs in bases:
        ccs = get_ccs_with_base(bs)
        len_ccs = len(ccs)
        if len_ccs > max_ccs:
            max_ccs = len_ccs
            ccss = [(cs[0][len(bs):], cs[1]) for cs in ccs] # strip base
    print('ccss', ccss)
    skip = []
    for ccs in ccss:
        ch = chain + ccs[0]
        print('adding:', *ccs, ch)
        insert_chains((ch, ccs[1]))
        skip.append(ch)
    commit()
    print('skip', skip)
    return(skip)

def fan(sectors, origin): # insert the details of every ancestor in the fan into the db
    skip = []
    for ch, x, y in sectors:
        chain = origin + ch
        if chain in skip: continue
        color = pg.pixel(x, y) # returns RGB triplet
        if color == (242, 242, 242) or color == (232, 232, 232) or color == (216, 216, 216): continue
        tup = grab(x, y, False)
        if len(tup) > 0:
            skip += insert(chain, tup)

def get_sectors():
    # fans should be set to 7 generations and sized to maximum on the screen
    #   while still having all sectors clickable
    # for calibration, determine x,y screen coordinates of the exact center (ring 0) of the fan
    #   followed by coordinates of the lower left sectors going outward from ring 1 to ring 6
    # then determine separately ring 6 lower right (xr, yr)
    coords = [(684, 535), (641, 502), (596, 526), (546, 545), (474, 576), (406, 608), (330, 640)]
    xr, yr = (1034, 640) 
    xc, yc = coords[0]
    ringmax = 7
    def radius_and_angle(tup):
        x, y = tup
        radius = math.sqrt((x - xc)**2 + (y - yc)**2)
        angle_rad = math.atan2(y - yc, x - xc)
        return radius, angle_rad
    rs = [0]
    for i in range(1, ringmax): rs.append(radius_and_angle(coords[i])[0])
    a_ll = radius_and_angle(coords[ringmax - 1])[1] # lower left outer ring sector angle
    da = (2 * math.pi - a_ll + radius_and_angle((xr, yr))[1]) / (2**(ringmax - 1) - 1)
    rings = []
    for ri in range(0, ringmax):
        ring = []
        factor = 2 ** (ringmax - 1 - ri)
        sa = a_ll + da * (factor - 1) / 2 
        for i in range(2**ri):
            a = sa + da * i * factor
            ring.append((int(xc + rs[ri] * math.cos(a)), int(yc + rs[ri] * math.sin(a))))
        rings.append(ring)
    sectors = ['']
    def tree(chain, length):
        if length == 0:
            sectors.append(chain)
            return
        tree(chain + 'F', length - 1)
        tree(chain + 'M', length - 1)
    for length in range(1, len(rings)): tree('', length)
    sec = 0
    for ri in range(0, len(rings)):
        for i in range(len(rings[ri])):
            sectors[sec] = (sectors[sec], ) + rings[ri][i]
            sec += 1
    return(sectors)

def main(title, generation, start, step):
    sectors = get_sectors()
    center = sectors.pop(0)
    found = False
    for window in pg.getAllWindows():
        if re.search('^' + title + '.*', window.title):
            found = True
            window.activate()
            time.sleep(2)
            break
    if not found:
        print('window not found:', title)
        sys.exit()
    def setup():
        pg.click(1275, 303); time.sleep(1) # full screen
        pg.click(1247, 137); time.sleep(1) # center the fan
    def status():
        print('#ancestors:', get_count('tree'), get_count('chains'))
    is_db = open_db('tree.db')
    if not is_db: # grab and insert home fan
        setup()
        tup = grab_center(center, '')
        insert('', tup)
        fan(sectors, '')
    status()
    gen = get_gen(generation)
    print(f"Generation {generation}: {len(gen)} ancestors")
    print(f"Gen {generation}: {start} to {start + step - 1} inclusive")
    for i in range(start, start + step):
        base = gen[i]
        if len(base) % 6 != 0 or not bool(re.match(r'[FM]*$', base)): crash('bad base')
        base_code = get_code(base)
        print(i, base, base_code)
        if len(base_code) != 8: crash('db error')
        pg.click(206, 62); time.sleep(0.2)
        pc.copy('https://www.familysearch.org/tree/pedigree/fanchart/' + base_code)
        pg.hotkey('ctrl', 'v'); time.sleep(0.2) # paste
        pg.press('enter'); time.sleep(4.6)
        setup()
        grab_center(center, base_code) # confirm
        fan(sectors, base)
        status()
    close_db()

title = 'Dr. John' # title of browser window displaying home fan
generation = 12 # generation must be multiples of 6
                # start at 6 after home fan is grabbed
start = 200 # start at 0
step = 227 # add step to start when ready for next round
# max (start + step) = number of ancestors at beginning of round
# currently len(gen) == 427 for generation = 12 
main(title, generation, start, step)
