from optparse import OptionParser
import components.zipfolder as zipfolder

parser = OptionParser()
parser.add_option('-s', '--src', dest='src')
parser.add_option('-d', '--dst', dest='dst')
(options, args) = parser.parse_args()

# handle required fields
if not options.src:
    parser.error('src is required')

if not options.dst:
    parser.error('dst is required')

zipfolder.zip(options.src, options.dst)