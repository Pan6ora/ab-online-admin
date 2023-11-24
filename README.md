
A web admin interface for Activity Browser Online.

# Activity Browser Online

Launch reproducible [Activity Browser](https://github.com/LCA-ActivityBrowser/activity-browser) sessions and distribute them using NoVNC.

# Developer quickstart

To ensure having the last bug fix of Activity Browser Online we are gonna use the git version:

```
clone repositories
git clone https://github.com/Pan6ora/activity-browser-online.git
git clone https://github.com/Pan6ora/ab-online-admin.git

# create conda environment
conda create -n ab-online-web -c pan6ora activity-browser-online
conda activate ab-online-web

# install local version of activity browser online
cd activity-browser-online
pip install -e .

# start ab-online-web development server
cd ../ab-online-admin
flask --app main run --debug
```

# To be implemented

- view existing sessions (name and infos)
- create/remove sessions
- change session setup
- add/remove databases