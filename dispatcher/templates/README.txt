Données brutes Hotline SOS Démocratie.
--------------------------------------

Le fichier CSV ci-joint contient les données brutes de la Hotline SOS Démocratie.

* Chaque ligne correspond à un appel de la hotline.
* Les demandes d'appels non répondues (ou non saisies) ne sont pas présentes.
* La liste des sujets avec codes est présente ci-dessous.
* Les codes des localité correspondent à la BDD présente sur OpenData.ml.
* Les numéros ne sont pas présents pour des raisons de confidentialité.

Le fichier CSV a été généré le: {{ created_on }}

Pour plus d'informations:
	Jokkolabs
	http://jokkolabs.ml
	rgaudin@jokkolabs.net
	renaud gaudin: (223) 73 12 08 96

Codes Sujets
------------
{% for topic in topics %}
{{ topic.slug }}: {{ topic.name|safe }} (cat: {{ topic.category }})
{% endfor %}
