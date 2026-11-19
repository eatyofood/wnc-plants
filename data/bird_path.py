"""Study path for North Carolina birds, most often seen first.

Same group size as the plant deck. Natives and established introduced
birds are mixed the way you meet them: yard birds first, then town
non-natives, then woods, water, mountains, and the coast.
"""

from learn_path import GROUP_SIZE  # noqa: F401

BIRD_ORDER = [
    # 1 Yard
    "northern-cardinal",
    "carolina-wren",
    "tufted-titmouse",
    "carolina-chickadee",
    "american-robin",
    # 2 Edges and feeders
    "blue-jay",
    "northern-mockingbird",
    "eastern-bluebird",
    "mourning-dove",
    "house-finch",
    # 3 Town birds, including introduced
    "european-starling",
    "house-sparrow",
    "rock-pigeon",
    "eurasian-collared-dove",
    "american-crow",
    # 4 Sparrows and winter flocks
    "eastern-towhee",
    "chipping-sparrow",
    "song-sparrow",
    "american-goldfinch",
    "dark-eyed-junco",
    # 5 Woodpeckers
    "downy-woodpecker",
    "red-bellied-woodpecker",
    "hairy-woodpecker",
    "northern-flicker",
    "pileated-woodpecker",
    # 6 Small climbers
    "white-breasted-nuthatch",
    "brown-headed-nuthatch",
    "brown-creeper",
    "blue-gray-gnatcatcher",
    "yellow-bellied-sapsucker",
    # 7 Fields and marshes
    "red-winged-blackbird",
    "brown-headed-cowbird",
    "eastern-meadowlark",
    "common-grackle",
    "killdeer",
    # 8 Vultures and hawks
    "turkey-vulture",
    "black-vulture",
    "red-tailed-hawk",
    "red-shouldered-hawk",
    "coopers-hawk",
    # 9 Eagles, kestrel, owls
    "american-kestrel",
    "osprey",
    "bald-eagle",
    "barred-owl",
    "great-horned-owl",
    # 10 Summer flyers
    "ruby-throated-hummingbird",
    "chimney-swift",
    "barn-swallow",
    "purple-martin",
    "eastern-phoebe",
    # 11 Forest song
    "wood-thrush",
    "scarlet-tanager",
    "indigo-bunting",
    "red-eyed-vireo",
    "ovenbird",
    # 12 Warblers
    "hooded-warbler",
    "pine-warbler",
    "yellow-rumped-warbler",
    "black-and-white-warbler",
    "common-yellowthroat",
    # 13 Mimics and flycatchers
    "gray-catbird",
    "brown-thrasher",
    "cedar-waxwing",
    "eastern-kingbird",
    "summer-tanager",
    # 14 Ducks and heron
    "canada-goose",
    "mallard",
    "wood-duck",
    "great-blue-heron",
    "belted-kingfisher",
    # 15 More water, including swans
    "green-heron",
    "great-egret",
    "double-crested-cormorant",
    "mute-swan",
    "tundra-swan",
    # 16 Game and night
    "wild-turkey",
    "northern-bobwhite",
    "eastern-screech-owl",
    "eastern-whip-poor-will",
    "chuck-wills-widow",
    # 17 Mountains
    "common-raven",
    "ruffed-grouse",
    "black-throated-blue-warbler",
    "black-throated-green-warbler",
    "winter-wren",
    # 18 Coast
    "brown-pelican",
    "laughing-gull",
    "ring-billed-gull",
    "royal-tern",
    "willet",
    # 19 More you will ask about
    "white-throated-sparrow",
    "muscovy-duck",
    "cattle-egret",
    "red-headed-woodpecker",
    "american-redstart",
]

BIRD_TITLES = {
    1: "Yard birds",
    2: "Edges and feeders",
    3: "Town birds, including introduced",
    4: "Sparrows and winter flocks",
    5: "Woodpeckers",
    6: "Nuthatches and small climbers",
    7: "Fields and marshes",
    8: "Vultures and hawks",
    9: "Eagles, kestrel, and owls",
    10: "Hummingbird, swift, and swallows",
    11: "Forest songbirds",
    12: "Warblers",
    13: "Mimics, waxwing, and flycatchers",
    14: "Ducks, goose, and heron",
    15: "More water birds and swans",
    16: "Turkey, quail, and nightjars",
    17: "Mountain birds",
    18: "Coast",
    19: "Winter sparrow, feral duck, and more",
}
