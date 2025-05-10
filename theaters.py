THEATERS = {
    'Grand Théâtre Lumière': '1 Bd de la Croisette, 06400 Cannes, France',
    'Debussy Theatre': '1 Bd de la Croisette, 06400 Cannes, France',
    'Agnès Varda Theatre': 'esplanade Georges Pompidou, 06400 Cannes, France',
    'Miramar': '35 Rue Pasteur, 06400 Cannes, France',
    'Bazin Theatre': '1 Bd de la Croisette, 06400 Cannes, France',
    'Buñuel Theatre': '1 Bd de la Croisette, 06400 Cannes, France',
    'Théâtre Croisette': '3 Rue Frédéric Amouretti 1',
    'Olympia 1': '5 Rue de la Pompe, 06400 Cannes, France',
    'Olympia 2': '5 Rue de la Pompe, 06400 Cannes, France',
    'Olympia 4': '5 Rue de la Pompe, 06400 Cannes, France',
    'Olympia 8': '5 Rue de la Pompe, 06400 Cannes, France',
    'Licorne': '25 avenue Francis Tonner 06150 Cannes La Bocca',
    'Raimu': 'Chemin de la Borde 06150 Cannes La Bocca',
    'Alexandre III': '19 Bd Alexandre III 06400 Cannes',
    'Studio 13': '23 Av. du Dr Raymond Picaud 06400 Cannes',
    'Arcades 1': '77 Rue Félix Faure 06400 Cannes',
    'Arcades 2': '77 Rue Félix Faure 06400 Cannes',
    'Cineum Screen X': '212 avenue Francis Tonner 06150 Cannes La Bocca',
    'Cineum Salle 3': '212 avenue Francis Tonner 06150 Cannes La Bocca',
    'Cineum Aurore': '212 avenue Francis Tonner 06150 Cannes La Bocca',
    'Cineum Imax': '212 avenue Francis Tonner 06150 Cannes La Bocca',
    'Palais K': '1 Bd de la Croisette, 06400 Cannes, France',
    'Plage Macé': 'Boulevard de la Croisette, 06400 Cannes, France'
}

def format_location(address):
    """Format address for ICS location field by escaping commas."""
    return address.replace(',', '\\,')

def get_theater_location(theater_name):
    """Get formatted location for a theater name."""
    if theater_name in THEATERS:
        return format_location(THEATERS[theater_name])
    return None 