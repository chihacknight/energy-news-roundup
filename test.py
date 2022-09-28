import locationtagger

entities = locationtagger.find_locations(text='i am living in')

print(len(entities.regions))
