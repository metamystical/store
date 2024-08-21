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
    open_db.conn = sqlite3.connect(db)
    open_db.curs = open_db.conn.cursor()
    if is_db: print('existing db opened')
    else:
        open_db.curs.execute("create table tree (code varchar(8) primary key not null unique, name text, birth_date text, birth_place text, death_date text, death_place text, ancestors text not null default '')")
        open_db.curs.execute('create table chains (chain text primary key not null unique, code varchar(8) not null)')
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
    exec('insert into tree (code, name, birth_date, birth_place, death_date, death_place, ancestors) values (?, ?, ?, ?, ?, ?, ?)', tup)

def insert_chains(tup):
    exec('insert into chains (chain, code) values (?, ?)', tup)

def get_code(chain): # returns code string or empty string if no code found
    res = exec_ret('select code from chains where chain = ?', (chain,))
    res = [r[0] for r in res]
    if len(res) == 0: return ''
    return res[0]

def get_gen(generation): # returns list of (chain, code) tuples or empty list
    return(exec_ret('select chain, code from chains where length(chain) = ? order by chain', (generation,)))

def get_ancestors(code): # returns ancestors string or empty string if no code found
    res = exec_ret('select ancestors from tree where code = ?', (code,))
    res = [r[0] for r in res]
    if len(res) == 0: return ''
    return res[0]

def put_ancestors(code, ancestors):
    open_db.curs.execute("update tree set ancestors = ? WHERE code = ?", (ancestors, code))

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

def backfill(chain, code):  # ancestors field in tree table can be cleared
                            #   after 6 or 12 generations processed
    generations = min(5, len(chain)) # 5 for a ringmax = 7 generation fan
    # insert code into ancestors field of up to 5 descendents
    for i in range(1, generations + 1):
        co = get_code(chain[:-i])
        tail = chain[-i:]
        index = sectors.seq.index(tail)
        ancestr = get_ancestors(co).split(';')
        ancestr.pop()
        el = len(ancestr)
        if index < el: ancestr[index] = code
        else:
            for j in range(el, index): ancestr.append('')
            ancestr.append(code)
        ancestors = ';'.join(ancestr) + ';'
        put_ancestors(co, ancestors)
    commit()

def insert(chain, tup):
    code = tup[0]
    if not is_code(code):
        insert_tree(tup + ('',))
        insert_chains((chain, code))
        backfill(chain, code)
        return([])
    # ancestor already existed; add new chain of this and every ancestor further up the tree
    #print('ancestor existed', code, chain)
    #print('adding:', chain, code)
    insert_chains((chain, code))
    ancestr = get_ancestors(code).split(';')
    ancestr.pop()
    el = len(ancestr)
    skip = []
    for i in range(len(ancestr)):
        co = ancestr[i]
        if co == '': continue
        tail = sectors.seq[i]
        ch = chain + tail
        #print('adding:', ch, co)
        insert_chains((ch, co))
        skip.append(ch)
    backfill(chain, code)
    #print('skip', skip)
    return(skip)

def fan(origin): # insert the details of every ancestor in the fan into the db
    skip = []
    for ch, x, y in sectors.secs:
        chain = origin + ch
        if chain in skip: continue
        color = pg.pixel(x, y) # returns RGB triplet
        if color == (242, 242, 242) or color == (232, 232, 232) or color == (216, 216, 216): continue
        tup = grab(x, y, False)
        if len(tup) > 0:
            skip += insert(chain, tup)

def sectors():
    # fans should be set to ringmax 7 generations and sized to maximum on the screen
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
    seq = ['']
    def tree(chain, length):
        if length == 0:
            seq.append(chain)
            return
        tree(chain + 'F', length - 1)
        tree(chain + 'M', length - 1)
    for length in range(1, len(rings)): tree('', length)
    sectors.seq = seq[1:]
    sec = 0
    for ri in range(0, len(rings)):
        for i in range(len(rings[ri])):
            seq[sec] = (seq[sec], ) + rings[ri][i]
            sec += 1
    sectors.center = seq.pop(0)
    sectors.secs = seq

def main(title, generation, start, end):
    sectors()
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
    if not open_db('tree.db'): # grab and insert home fan
        setup()
        tup = grab_center(sectors.center, '')
        insert('', tup)
        fan('')
    status()
    gen = get_gen(generation)
    #for g in gen: backfill(*g) # used once when backfill introduced gen24
    print(f"Generation {generation}: {len(gen)} remaining lines")
    print(f"Gen {generation}: {start} to {end - 1} inclusive")
    for i in range(start, end):
        base = gen[i][0]
        if len(base) % 6 != 0 or not bool(re.match(r'[FM]*$', base)): crash('bad base')
        base_code = get_code(base)
        print(i, base, base_code)
        if len(base_code) != 8: crash('db error')
        pg.click(206, 62); time.sleep(0.2)
        pc.copy('https://www.familysearch.org/tree/pedigree/fanchart/' + base_code)
        pg.hotkey('ctrl', 'v'); time.sleep(0.2) # paste
        pg.press('enter'); time.sleep(4.6)
        setup()
        grab_center(sectors.center, base_code) # confirm
        fan(base)
        status()
    close_db()
    print(f"When this round is complete to {generation+6} generations, the maximum number of ancestors is {2*(2**(generation+6) - 1)}")

title = 'Dr. John' # title of browser window displaying home fan
generation = 24 # generation must be multiples of 6
                # start at 6 after home fan is grabbed
start = 43 # start at 0
end = 100 # exclusive; replace start with end when ready for next round
# max end = number of ancestors at beginning of round
# currently len(gen) == 36506 for generation = 24
main(title, generation, start, end)
