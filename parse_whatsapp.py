import datetime
import re
import sys
import operator
import stop_words

pattern = re.compile('^(.* .*) - (.*?): (.*)$')
changed_pattern = re.compile('^(.* .*) - (.*?) changed .*$')

messages = []

attributed_tokens = []
token_counts = {}

stops = set(stop_words.get_stop_words('en'))

with open('stopwords.txt', 'r') as f:
    for line in f:
        line = line.strip()
        if len(line) > 0:
            stops.add(line)

stops.add('<media')
stops.add('omitted>')
for x in xrange(20):
    stops.add(str(x))

with open(sys.argv[1], 'r') as f:
    for line in f:
        line = line.strip()
        # Line like this "2016-09-17, 12:05 - Edward Guo: It's been 3 years and a month"
        match = pattern.match(line)
        changed_match = changed_pattern.match(line)
        if match:
            whatsapp_format_datetime = match.group(1)
            speaker = match.group(2)
            message_time = datetime.datetime.strptime(whatsapp_format_datetime, '%Y-%m-%d, %H:%M')
            message = {}
            message['time'] = message_time
            message['speaker'] = speaker
            messages.append(message)
            tokens = match.group(3).split()
            for t in tokens:
                t = t.lower()
                t = t.strip(',')
                if t in stops:
                    continue
                attributed_tokens.append({'speaker': speaker, 'token': t})
                try:
                    token_counts[t] += 1
                except KeyError:
                    token_counts[t] = 1
        elif changed_match:
            pass
        else:
            pass

total = len(messages)
total_token_count = len(attributed_tokens)

# Find distribution over hours
hour_counts = dict([(x, 0) for x in xrange(24)])
for m in messages:
    hour_counts[m['time'].hour] += 1

speaker_list = set([m['speaker'] for m in messages])
speaker_counts = dict([(x, 0) for x in speaker_list])
for m in messages:
    speaker_counts[m['speaker']] += 1

print 'When do we chat?'
for hc in hour_counts.iteritems():
    print '    {}:00-{}:00: {:.2%}'.format(hc[0], hc[0]+1, hc[1] / float(total))

print

print 'Who chats?'
for sc in sorted(speaker_counts.iteritems(), key=operator.itemgetter(1), reverse=True):
    print '    {}: {:.2%}'.format(sc[0], sc[1] / float(total))

print 

print 'What do we say?'
for t in sorted(token_counts.iteritems(), key=operator.itemgetter(1), reverse=True)[:50]:
    print '    {} {} times'.format(t[0], t[1])

token_percents = dict([(tc[0], tc[1] / float(total_token_count)) for tc in token_counts.iteritems()])

speaker_token_counts = dict([(x, {}) for x in speaker_list])
for at in attributed_tokens:
    speaker = at['speaker']
    token = at['token']
    try:
        speaker_token_counts[speaker][token] += 1
    except KeyError:
        speaker_token_counts[speaker][token] = 1

print

speaker_total_words = dict([(x, 0) for x in speaker_list])
for at in attributed_tokens:
    try:
        speaker_total_words[at['speaker']] += 1
    except KeyError:
        speaker_total_words[at['speaker']] = 1

speaker_token_uniqueness = dict([(x, {}) for x in speaker_list])
for speaker in speaker_list:
    for token, count in speaker_token_counts[speaker].iteritems():
        ratio = count / float(speaker_total_words[speaker])
        global_ratio = token_percents[token]
        uniqueness = ratio / global_ratio
        if (count >= 2):
            speaker_token_uniqueness[speaker][token] = uniqueness * count

for speaker in speaker_list:
    print '{}\'s words (word and how much more likely {} is to say this word than the rest of us)'.format(speaker, speaker)
    for t in sorted(speaker_token_uniqueness[speaker].iteritems(), key=operator.itemgetter(1), reverse=True)[:20]:
        print '    {} {}'.format(t[0], t[1])
