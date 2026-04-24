from bs4 import BeautifulSoup

def nettoyer_html(html_content):
    # Initialiser le parseur
    soup = BeautifulSoup(html_content, "html.parser")

    # Liste des balises à supprimer
    balises_a_retirer = ["script", "style", "svg"]

    for balise in soup(balises_a_retirer):
        # .decompose() retire la balise et tout ce qu'elle contient du document
        balise.decompose()

    # Retourner le HTML propre sous forme de chaîne
    return str(soup)


def chunk_html_content(html_string, max_chunk_size=4000):
    """
    Découpe un contenu HTML en morceaux (chunks) en respectant l'intégrité
    des balises tant que possible.
    """
    soup = BeautifulSoup(html_string, "html.parser")

    # On travaille sur le contenu du body s'il existe, sinon sur la soupe entière
    container = soup.find('body') if soup.find('body') else soup

    chunks = []
    current_chunk = ""

    # On itère sur les éléments directs (enfants) du conteneur
    for element in container.contents:
        # On convertit l'élément en string (balise + contenu)
        element_str = str(element)

        # Cas particulier : l'élément seul est déjà plus gros que la taille max
        if len(element_str) > max_chunk_size:
            # Si on a déjà accumulé du texte, on le sauvegarde d'abord
            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = ""

            # On découpe l'élément géant par force brute (ou par récursion si besoin)
            # Ici, on le découpe simplement en tranches pour ne pas bloquer
            for i in range(0, len(element_str), max_chunk_size):
                chunks.append(element_str[i:i + max_chunk_size])
            continue

        # Si ajouter cet élément dépasse la limite, on ferme le chunk actuel
        if len(current_chunk) + len(element_str) > max_chunk_size:
            chunks.append(current_chunk.strip())
            current_chunk = element_str
        else:
            current_chunk += element_str

    # Ne pas oublier le dernier morceau
    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks



with open("html_test.html", "r") as f:
    html_sale = f.read()
html_propre = nettoyer_html(html_sale)
mes_chunks = chunk_html_content(html_propre, max_chunk_size=4000)

for i, chunk in enumerate(mes_chunks):
    print(f"--- Chunk {i + 1} (Taille: {len(chunk)}) ---")
    # print(chunk) # À envoyer à ton IA

print(mes_chunks[4])
