# spark-cloud-omc
## A. Introduction
Cette réalisation est un embryon de l'application **Spark EC2** pour **Openstack**. Elle est relative à l'installation de **Spark Cluster Manager Standalone** pour gérer des ressources de traitements distribuées et s'appuie sur **HDFS** d'Hadoop pour gérer les données distribuées. Elle reprend les concepts de la réalisation de "_ezhaar_" (disponible sur GitHub) qui est constituée de 2 parties:

1. une première relative à la création d'une image de référence pour des VM **Openstack** (master et slaves Spark) avec les composants suivants d'installés et de configurés: **Spark**, **Hadoop**, **Yarn**, **Scala**, ...,

2. une deuxième relative à une copie minimaliste du script Python de **Spark EC2** basée sur des instanciations (master et slave(s)) de l'image de référence **Openstack** produite à l'étape précédente.

Elle a été adaptée uniquement pour montrer la faisabilité aisée du déploiement d'un cluster **Spark** sur **Openstack**. Le code est une première itération qui doit être amélioré sur les aspects qualité du code, sécurité et fonctionnalités. A titre d'exemple, il est nécessaire de vérifier que les quotas en ressources du tenant ne sont pas toutes consommées (ex: adresses IP flottantes, RAM, etc.). En l'état, le code permet de mettre facilement à disponibilité un cluster **Spark** (le démarrer et supprimer uniquement) pour par exemple dérouler des sessions de formation. La réalisation n'est naturellement pas destinée à être déployée en production.

## B. Construction d'une image de référence
Pour instancier un cluster *Spark* (ex: 1 master et 2 slaves) dans l'implémentation d'**Openstack** retenue (release **Icehouse**), il faut procéder comme ceci depuis un poste quelconque sur lequel, les commandes **CLI** et le **SDK** Python (2.7) d'**Openstack** sont présents et configurés:

1) Lancer le script Python **create_image.py** avec la syntaxe suivante (OS **Ubuntu 14.04** LTS Server associé à l'image):

```
    $ tar czfv config_files.tar.gz config_files <CR>
    $ python create_image.py <CR>
    usage: create_image.py vm-name key-name userdata-file
        vm-name: nom de la VM à instancier
        key-name: nom du fichier (présent sous le répertoire courant) relatif à la clé privée d'accès root à la VM
        userdata-file: fichier de commandes à passer à Cloud-init
    
    $ python create_image.py LB-VM04 KP-OMC-01 udata.txt <CR>
```

  En cas de dysfonctionnement se connecter à la VM pour vérifier le déroulement du script Shell (udata.txt) à l'aide du fichier "/root/bootVM.log") de la façon suivante:

```
    $ ssh -i KeyfileName root@VMfloatingIP <CR>
    root@lb-vm04# tail -f /root/bootVM.log <CR>
```

2) Créer une image VM de référence nécessaire aux instances de VM pour le cluster Spark.


```
    $ nova image-create LB-VM04 LB-VM04-R01 <CR>
```
## C. Instanciation du **Cluster Spark** avec master et slave(s)
1) Instancier le cluster **Spark** à l'aide du script Python "spark-openstack" avec la syntaxe suivante:

```
    $ spark-openstack launch -s 2 -k KP-OMC-01 -i LB-VM04-R01 -c LB-VM04 <CR>
    ...
    $ nova list | grep grep LB-VM04 <CR>
    ...
```

2) Démarrer les services **Hadoop**, **YARN**, **Spark and Co** en se connectant à la VM master du cluster et en utilisant les fonctions du fichier "fabfile.py", comme ceci. Le script Python "fabfile.py" associé au master (compte: **hduser**) permet selon les arguments donnés :

  - de copier les fichiers de configuration pour **Hadoop**, **Yarn** et **Spark** sur l'ensemble des noeuds du cluster,
  - de formater l'espace **Hadoop** associé au namenode,
  - de démarrer **Hadoop**,
  - de créer un répertoire utilisateur (hduser) sur **HDFS**,
  - de démarrer **Yarn**,
  - de démarrer **Spark** (master et slave(s)).

3) Initialisation et lancement du cluster. La connexion au master et les commandes Python de gestion du cluster sont données ci-dessous pour exemple.

```
    $ chmod 0600 KeyFileName <CR>
    $ ssh -i KeyFileName root@$VMfloatingIP <CR>
    root@lb-vm04-master# fab -l <CR>
    ...

    # test (préalable) les connexions SSH avec les slaves (workers Spark)
    root@lb-vm04-master# fab test_conn <CR>
    lb-vm04-slave-94e538d0-5b19-457e-8e72-939647fb68d2
    lb-vm04-slave-4131aab9-c505-4f75-9f34-6dd884258941
    ...
    
    # initialisation du cluster 
    root@lb-vm04-master# fab init_cluster <CR>
    ...

    # démarrage des services Hadoop (DFS & YARN)
    root@lb-vm04-master# fab start_hadoop <CR>
    ...

    # démarrage des services Spark (Master et Slave(s))
    root@lb-vm04-master# fab start_spark <CR>
    ...
```

## D. Conclusion
A ce stade, on peut utiliser et gérer le cluster à l'aide des différentes interfaces. Pour ce faire, l'utilisation de notebooks est appropriée. Cette petite adaptation est relative à un embryon de portage du code **EC2 Spark** sur **Openstack Spark**. Un travail approfondi doit être mené pour réellement porter le code **EC2 Spark** pour **Openstack Spark**. La charge de travail est de l'ordre d'une semaine (tests et documentations compris).
