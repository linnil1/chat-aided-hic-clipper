def hic_ame_keyword(i):
    return "hic" == i['message'].lower() or \
           ":_hic1::_hic2::_hic3:" == i['message']


def hic_ubye_keyword(i):
    # this is enough in chinese chat
    return "hic" in i['message'].lower()
