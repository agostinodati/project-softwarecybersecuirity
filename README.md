# Progetto Software Cybersecurity

### Implementazione di una biglietteria online tramite blockchain

##### Guida installazione e utilizzo (windows)

1. Scaricare e installare [XAMPP](https://www.apachefriends.org/it/index.html)
    - Importare in phpmyadmin il file *cybersecurity_project.sql*
2. Installare [WSL2](https://github.com/SensorsINI/DHP19/blob/master/Eval_2D_triangulation_and_3D_tutorial.ipynb)
    - Seguire le istruzioni di “Manual Installation Steps” fino al passo 6 escluso
3. Installare [Docker](https://docs.docker.com/docker-for-windows/install/)
    - Scaricare l’installer e seguire le istruzioni (verificato con Docker 3.3.1)
    - Verificare di cliccare sulla check box «Use WSL 2 based engine»
    - Al termine dell’installazione, è necessario riavviare
4. Installare [NodeJS](https://nodejs.org/it/) per Windows
5. Installare quorum-wizard
    - Aprire terminale di Windows
    - Eseguire, optando per docker-compose quando richiesto:
  ```
  npx quorum-wizard
  cd networks/<nome_network>/
  start.cmd
  ``` 
6. Importare il progetto nel proprio IDE ed eseguire le seguenti installazioni:
  ```
  pip install Flask 
  pip install mysql-connector-python 
  pip install --upgrade Pillow 
  pip install web3 
  pip install cryptography
  ```
7. Eseguire il *main* e aprire l'indirizzo nella console




