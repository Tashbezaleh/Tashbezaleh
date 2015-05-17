# -*- coding: utf-8 -*-

import urllib, json, re
import databaseUtils

#
# methods for online search
#
def get_matches(res, regex):
    '''Returns a list of all possible matches of 'regex' in 'res'.'''
    res=res.split()
    res=map(lambda i: ''.join([x for x in i if x in r'אבגדהוזחטיכלמנסעפצקרשתץףםךן']), res)
    res=filter(lambda x: len(x.strip()) > 0, res)
    res = filter(lambda x: regex.match(x), res)
    return res

def add_to_hist(hist, res, regex):
    '''Adds the matches of 'regex' in 'res' to the histogram 'hist'.'''
    res = get_matches(res, regex)
    for r in res:
        hist[r] = 1 + (hist[r] if r in hist else 0)

def style(hist):
    '''Return a sorted list of the 10 most frequent occurences in 'hist'.'''
    max_num_of_options = 5
    items = sorted(hist.items(), key=lambda t: -t[1])[:max_num_of_options]
    n_matches = sum(t[1] for t in items)
    return [(k, 100.0 * v / n_matches) for (k, v) in items]
        
def find_online(definition, guess):
    '''Searches for 'definition' in google and then scans for 'guess' (compiled regex).'''
    query = urllib.urlencode({u'q': definition})
    url = 'http://ajax.googleapis.com/ajax/services/search/web?v=1.0&%s' % query
    search_response = urllib.urlopen(url)
    search_results = search_response.read()
    results = json.loads(search_results)
    data = results['responseData']
    if data == None:
        return 'Failure'
    hits = data['results']
    histogram = dict()
    for h in hits:
        res = urllib.urlopen(urllib.unquote(h['url'])).read()
        add_to_hist(histogram, res, guess)
    #return style(histogram)

    # removing the freqs
    answers = map(lambda t: t[0], style(histogram))
    return [databaseUtils.Answer(answer, definition, 'הפותר האוטומטי', 0) for answer in answers]


##def deep_online_search(definition, guess):
##    hist = style(find_online(definition + ' תשבץ', guess))[:5]
##    regex = r'|'.join(definition.split())
##    lst = []
##    for (w, f) in hist:
##        sub_hist = find_online(w, regex)
##        lst += [(w, sum(sub_hist.values()))]
##    total = sum(f for (w, f) in lst)
##    return sorted([(w, 100.0 * f / total) for (w,f) in lst], key = lambda t: -t[1])
        
# def search_guess_in_sols(regex):
#     hist = dict()
#     add_to_hist(hist, defs, regex)
#     return hist

# def find_offline(definition, guess):
#     if definition in defs_to_sols:
#         return filter(lambda w: guess.match(w), defs_to_sols[definition])
#     return []

def find(definition, guess, search_online):
    lst = databaseUtils.find_in_ndb(definition, guess)
    if lst:
        return lst, False#[(w, 100.0 / len(lst)) for w in lst], False
    if search_online:
        return find_online(definition, guess), True
    return [], search_online

# def html_solve(definition , guess, search_online=True):
#     '''Solves 'definition' using 'guess' (compiled regex) and returns embeddable html.'''
#     results, online = find(definition, guess, search_online)
#     if results and results != 'Failure':
#         return '</br>'.join(map(lambda t: '%s: %.2f%%' % t, results)), online
#     return 'לא נמצאו תוצאות', online

def user_pat_to_regex(pat):
    return re.compile('^' + pat.replace('?', '..').encode('utf') + '$', re.UNICODE)