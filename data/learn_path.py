"""Study path: most-common WNC plants first, in groups of 5.

Order is what you are most likely to meet on roads, trails, and woods edges
in the lower and middle mountains, then less common, high-elevation, and
rare species. Invasives are mixed in at the point you would actually see them.
"""

LEARN_ORDER = [
    # 1 Everyday trees
    "red-maple",
    "tulip-poplar",
    "flowering-dogwood",
    "eastern-white-pine",
    "sourwood",
    # 2 Oaks and the rash
    "northern-red-oak",
    "white-oak",
    "chestnut-oak",
    "black-cherry",
    "poison-ivy",
    # 3 Trail shrubs and vines
    "mountain-laurel",
    "rosebay-rhododendron",
    "virginia-creeper",
    "japanese-honeysuckle",
    "eastern-hemlock",
    # 4 Common hardwoods
    "pignut-hickory",
    "american-beech",
    "sassafras",
    "blackgum",
    "eastern-redbud",
    # 5 Roadsides
    "black-locust",
    "eastern-red-cedar",
    "american-sycamore",
    "pokeweed",
    "jewelweed",
    # 6 Invasives you will see
    "mimosa",
    "tree-of-heaven",
    "kudzu",
    "chinese-privet",
    "japanese-stiltgrass",
    # 7 Understory trees
    "serviceberry",
    "striped-maple",
    "american-holly",
    "persimmon",
    "sweet-birch",
    # 8 Mountain shrubs
    "catawba-rhododendron",
    "flame-azalea",
    "spicebush",
    "witch-hazel",
    "highbush-blueberry",
    # 9 Spring woods floor
    "mayapple",
    "jack-in-the-pulpit",
    "christmas-fern",
    "large-flowered-trillium",
    "bloodroot",
    # 10 Cove hardwoods
    "sugar-maple",
    "yellow-buckeye",
    "carolina-silverbell",
    "yellow-birch",
    "american-hornbeam",
    # 11 Climbing thickets
    "trumpet-creeper",
    "english-ivy",
    "oriental-bittersweet",
    "multiflora-rose",
    "autumn-olive",
    # 12 Yard-escape invasives
    "callery-pear",
    "princess-tree",
    "garlic-mustard",
    "periwinkle",
    "japanese-barberry",
    # 13 More spring plants
    "trout-lily",
    "red-trillium",
    "ramps",
    "wild-ginger",
    "partridgeberry",
    # 14 Summer wildflowers
    "bee-balm",
    "cardinal-flower",
    "joe-pye-weed",
    "black-eyed-susan",
    "butterfly-weed",
    # 15 More trees
    "black-walnut",
    "pawpaw",
    "fraser-magnolia",
    "cucumber-magnolia",
    "virginia-pine",
    # 16 Fruiting shrubs
    "elderberry",
    "sweetshrub",
    "hearts-a-bustin",
    "smooth-sumac",
    "winterberry",
    # 17 Forest floor
    "galax",
    "wintergreen",
    "fire-pink",
    "wild-columbine",
    "cinnamon-fern",
    # 18 Remaining invasives
    "japanese-knotweed",
    "burning-bush",
    "chinese-wisteria",
    "nandina",
    "butterfly-bush",
    # 19 High peaks and timber
    "shortleaf-pine",
    "fraser-fir",
    "red-spruce",
    "american-basswood",
    "white-ash",
    # 20 Specialty trees and native vines
    "table-mountain-pine",
    "carolina-hemlock",
    "shagbark-hickory",
    "american-chestnut",
    "coral-honeysuckle",
    # 21 Medicinal, rare, last ferns
    "passionflower",
    "crossvine",
    "black-cohosh",
    "american-ginseng",
    "maidenhair-fern",
    # 22 Last two
    "oconee-bells",
    "chinese-silvergrass",
]

GROUP_TITLES = {
    1: "Everyday trees",
    2: "Oaks, cherry, and poison ivy",
    3: "Laurel, rhododendron, common vines",
    4: "Hickory, beech, redbud",
    5: "Roadsides and wet edges",
    6: "Common invasives",
    7: "Understory trees",
    8: "Mountain shrubs",
    9: "Spring woods floor",
    10: "Cove hardwoods",
    11: "Climbing thickets",
    12: "Yard-escape invasives",
    13: "More spring plants",
    14: "Summer wildflowers",
    15: "Magnolias, pawpaw, pines",
    16: "Fruiting shrubs",
    17: "Forest floor",
    18: "Remaining invasives",
    19: "High peaks and timber",
    20: "Specialty trees and native vines",
    21: "Medicinal and rare",
    22: "Rarest last",
}

GROUP_SIZE = 5
