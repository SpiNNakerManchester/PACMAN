from pacman.model.placements import PlacementsCopy, Placements

class IsomorphicChecker(object):
    def __init__(self):
        if Placements._placements() == PlacementsCopy._placements():
            print "nyah nyah"
        else:
            print "aw fuck this"

