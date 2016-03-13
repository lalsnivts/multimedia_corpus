import codecs, time

class Logger:
    def __init__(self, outFilename=u'log.txt'):
        self.logQueue = []
        self.outFilename = outFilename
        try:
            f = codecs.open(outFilename, 'w', 'utf-8-sig')
            f.close()
        except IOError:
            self.add_message(u'Logger initialization error: couldn\'t open file.')

    def add_message(self, message):
        self.logQueue.append((time.clock(), message))

    def flush(self):
        try:
            f = codecs.open(self.outFilename, 'a', 'utf-8-sig')
            for message in self.logQueue:
                f.write(str(message[0]) + u'\t' + message[1] + u'\r\n')
            f.close()
            self.logQueue = []
        except IOError:
            self.add_message(u'Logger flush error: couldn\'t open file.')
