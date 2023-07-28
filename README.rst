=============
game_lookup
=============

A tool for looking up games on IGDB and populating a Google sheet withh descriptions and links

Installation
=============

Requirements
++++++++++++

- Python 3.8+ Python_



Windows Installation
+++++++++++++++++++++

Download the package from GitHub_ and unzip it.

Copy your `google_client_secret.json` file to the `src/conf/` folder

Rename `src/conf/twitch.py.example` to `twitch.py` and update with your client ID and client secret

Open a command prompt and change directory to the unzipped project

Run the following command::

  pip install --user --use-feature=in-tree-build .


You will likely see a WARNING message, similar to the following

``WARNING: The script game-lookup.exe is installed in
'C:\Users\%USERNAME%\AppData\Local\Packages\PythonSoftwareFoundation.Python.3
.9_qbz5n2kfra8p0\LocalCache\local-packages\Python39\Scripts' which is not on PATH``

Add this to your path with the following command::

 setx PATH "C:\Users\%USERNAME%\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.9_qbz5n2kfra8p0\LocalCache\local-packages\Python39\Scripts;%PATH%"

*Make sure that you copy and paste the path from your error message, and
ensure that ;%PATH% is added to the end*

Restart your computer to make sure that the %PATH% is loaded correctly

Using
=====

From a command prompt run game-lookup.exe 

After logging into Google, select a sheet where all game names to look up are in column A

.. _GitHub: https://github.com/djnrrd/game_lookups/releases
.. _Python: https://www.python.org/downloads/