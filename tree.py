import pyautogui as pg
import pyperclip as pc
import re
import math
import time
import sys
import os
import sqlite3

code_pattern = re.compile('^[A-Z1-9]{4}-[A-Z1-9]{3}$')

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

def delete_tree(code):
    return(exec('delete from tree where code=?', (code,)))

def update_tree_code(old, new):
    return(exec('update tree set code = ? where code = ?', (new, old)))

def update_tree_tup(code, tup):
    return(exec('update tree set name = ?, birth_date = ?, birth_place = ?, death_date = ?, death_place = ? where code = ?', tup[1:] + (code,)))

def get_name(code):
    res = exec_ret('select name from tree where code = ?', (code,))
    res = [r[0] for r in res]
    if len(res) == 0: return ''
    return res[0]

def get_ancestors(code): # returns ancestors string or empty string if no code found
    res = exec_ret('select ancestors from tree where code = ?', (code,))
    res = [r[0] for r in res]
    if len(res) == 0: return ''
    return res[0]

def put_ancestors(code, ancestors):
    open_db.curs.execute("update tree set ancestors = ? WHERE code = ?", (ancestors, code))

def insert_chains(tup):
    exec('insert into chains (chain, code) values (?, ?)', tup)

def update_chains(old, new):
    return(exec('update chains set code=? where code=?', (new, old)))

def get_chains(code):
    res = exec_ret('select chain from chains where code = ?', (code,))
    return(', '.join([r[0] for r in res]))

def get_code(chain): # returns code string or empty string if no code found
    res = exec_ret('select code from chains where chain = ?', (chain,))
    res = [r[0] for r in res]
    if len(res) == 0: return ''
    return res[0]

def get_gen(generation): # returns list of (chain, code) tuples or empty list
    return(exec_ret('select chain, code from chains where length(chain) = ? order by chain', (generation,)))

def get_count(table):
    return(exec_ret(f'select count(*) from {table}', ())[0][0])

def crash(mess):
    print(mess); close_db(); sys.exit()

def grab(x, y): # get the details of an ancestor at x,y; return tuple, could be ()
    def get_line(index): # statics got_lines and lines are lost when grab() returns
        try: line = lines[index]
        except Exception as e: crash('line not found at index ' + str(index))
        return(line)
    for round in range(4): # three tries waiting for detail to appear and be copied
        if round == 3: return(())
        pg.click(x, y); time.sleep(0.5) # open detail popup
        if pg.pixel(1010, 122) == (221, 223, 223): continue # check colored bar
        pc.copy('xyzzy')
        pg.hotkey('ctrl', 'a'); pg.hotkey('ctrl', 'c') # select all, copy
        lines = pc.paste().splitlines()
        if len(lines) >= 39: break
    offset = 0
    pattern = re.compile('^[A-Z1-9]{4}-[A-Z1-9]{3}$') # for code
    code = get_line(offset + 28)
    if not bool(pattern.match(code)):
        offset = 1
        code = get_line(offset + 28)
        if not bool(pattern.match(code)): return(())
    name = get_line(offset + 26)
    if name.capitalize() == 'Unknown': return(())
    f = []
    for i in range(offset + 32, offset + 39):  f.append(get_line(i))
    # find markers
    birth = -1; death = -1; person = -1
    for i in range(0, len(f)):
        for j in ['Birth:', 'Christening:']:
            if f[i][:len(j)] == j: birth = i; f[i] = f[i][len(j):].strip()
        for j in ['Death:', 'Burial:', 'Living']:
            if f[i][:len(j)] == j: death = i; f[i] = f[i][len(j):].strip()
        if f[i] == 'Person': person = i - 2
    if birth == -1: crash('birth anomoly')
    if death == -1: crash('death anomoly')
    if person == -1: crash('person anomoly')
    def get_pair(start, end):
        date = ''; place = ''
        def anomolies(a):
            return(bool(re.search(r'\d', a)) or a.capitalize() in ['', 'Deceased', 'Unknown', 'Sep', '?', 'Date not given'])
        if end > start:
            a = f[start]
            if anomolies(a):
                date = a
                if end > start + 1: place = f[start + 1]
            else:
                if end > start + 1 or anomolies(a): crash('date anomoly:' + a)
                place = a
        return((date, place))
    birth_date, birth_place = get_pair(birth, death)
    death_date, death_place = get_pair(death, person)
    return((code, name, birth_date, birth_place, death_date, death_place))

def url(mode, code, delay):
        pg.press('esc'); pg.click(172, 60); time.sleep(1)
        if mode: mode = 'person/details/'
        else: mode = 'pedigree/fanchart/'
        pc.copy('https://www.familysearch.org/tree/' + mode + code)
        pg.hotkey('ctrl', 'v'); time.sleep(1) # paste
        pg.press('enter'); time.sleep(delay)

def copy(al):
    if al: pg.hotkey('ctrl', 'a')
    pg.hotkey('ctrl', 'c'); time.sleep(0.2)

def setup(): # must first manually position the fan by hitting home then scroll
    pg.click(1213, 264); time.sleep(1) # dismiss (temporary)
    pg.click(1213, 264); time.sleep(1) # full screen
    pg.click(684, 525); time.sleep(1.5) # open sidebar

def merger(old, new):
    if not is_code(old): crash('code not found: ' + old)
    print('Old name: ' + get_name(old))
    print('Old chains: ' + get_chains(old))
    print('New name: ' + get_name(new))
    print('New chains: ' + get_chains(new))
    if is_code(new):
        print('New already exits: ' + new)
        print('deleting old from tree...')
        if not delete_tree(old): crash('failed to delete from tree: ' + old)
    else:
        print('updating tree...')
        if not update_tree_code(old, new): crash('failed to update tree: ' + old)
    print('updating old chains...')
    if not update_chains(old, new): crash('failed update chains: ' + old)
    commit()
    print('Old name: ' + get_name(old))
    print('Old chains: ' + get_chains(old))
    print('New name: ' + get_name(new))
    print('New chains: ' + get_chains(new))

def merge(code):
    url(True, code, 8)
    pg.press('esc'); copy(True)
    lines = pc.paste().splitlines()
    p = re.compile('This person was deleted by merge.')
    for line in lines:
        if bool(p.match(line)):
            pg.press('esc'); pg.click(729, 448); time.sleep(4)
            pg.click(206, 62); time.sleep(0.2)
            copy(False)
            match = code_pattern.search(pc.paste()[-8:])
            if match:
                match = match.group(0)
                merger(code, match)
                url(False, match, 5)
                setup()
                tup = grab_center(match)
                update_tree_tup(match, tup)
                return(match)
            break
    crash('fan not loaded')

def grab_center(code): # crash upon fail
    round = 0
    while True: # three tries moving slightly in center to get to link
        if round == 3:
            code = merge(code)
            round = 0
        offset = -4 + 8 * round # in case of no last name
        ch, x, y = sectors.center
        tup = grab(x, y + offset)
        if len(tup) == 0:
            time.sleep(0.4)
            round += 1
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
        if pg.pixel(x, y) in [(242, 242, 242), (221, 223, 223)]: continue
        tup = grab(x, y)
        if len(tup) > 0: skip += insert(chain, tup)

def sectors():
    # fans should be set to ringmax 7 generations and sized to maximum on the screen
    #   while still having all sectors clickable
    # for calibration, determine x,y screen coordinates of the exact center (ring 0) of the fan
    #   followed by coordinates of the lower left sectors going outward from ring 1 to ring 6
    # then determine separately ring 6 lower right (xr, yr)
    coords = [(502, 525), (457, 492), (417, 509), (365, 532), (300, 561), (236, 591), (172, 618)]
    xr, yr = (831, 623)
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
    def status():
        print('#ancestors:', get_count('tree'), get_count('chains'))
    if not open_db('tree.db'): # grab and insert home fan
        setup()
        tup = grab_center('')
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
        url(False, base_code, 5)
        setup()
        grab_center(base_code) # confirm
        fan(base)
        status()
    close_db()
    print(f"When this round is complete to {generation+6} generations, the maximum number of ancestors is {2*(2**(generation+6) - 1)}")

title = 'Dr. John' # title of browser window displaying home fan
generation = 24 # generation must be multiples of 6
                # start at 6 after home fan is grabbed
start = 4500 # start at 0
end = 4501 # exclusive; replace start with end when ready for next round
# max end = number of ancestors at beginning of round
# currently len(gen) == 36506 for generation = 24
main(title, generation, start, end)
