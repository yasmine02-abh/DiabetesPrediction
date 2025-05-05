import requests

def chercher_aliment(nom):
    url = f"https://world.openfoodfacts.org/cgi/search.pl?search_terms={nom}&search_simple=1&action=process&json=1"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        produits = data.get("products", [])
        if produits:
            produit = produits[0]
            return {
                'nom': produit.get('product_name', nom),
                'calories': produit.get('nutriments', {}).get('energy-kcal_100g', 0)
            }
    return None
