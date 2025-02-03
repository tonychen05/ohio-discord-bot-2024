## Welcome to the repository for the OHI/O Discord bot!

Here are instructions on how to set up the repository on your own machine.

Note that these instructions assume that you already have...

- A GitHub account. To create a GitHub account, click "sign up" in the top right corner of any page on GitHub.

- Git installed on your PC. You can download the latest version of Git at [git-scm.com/downloads](https://git-scm.com/downloads).

- Python installed on your PC. You can download the latest version of Python at [www.python.org/downloads](https://www.python.org/downloads/).

- Some basic command line knowledge. If this is a roadblock for you, then you can ask another tech committee member for help.

### 1. Fork this repository ("repo" for short).

Near the top-right corner of this repo's GitHub page will be a button labeled **Fork**. Click it and follow the on-screen instructions to create a fork of this repo.

A fork is a copy of the repo under your own account. Creating a fork gives you the freedom to play around with the code, since changes won't affect the production code.

### 2. Clone the repository to your computer.

"Cloning" is the process of creating a local copy of a repo. Right now, your fork only exists in the cloud on GitHub. If you want to be able to edit the code in your fork on your PC, you need a copy of your fork on your PC.

[The GitHub Docs article on cloning a repo](https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository) covers some of the different ways you can clone a repo. The following instructions will tell you how to use the command line to clone a repo, as you will be doing later steps via the command line as well.

First, you should get the URL for the repo by clicking the green **Code** button near the top right of the GitHub page for the fork you created in step 1.

Now you should open a terminal window. Navigate to a directory where you would like to keep the local repo. (You should pick a directory that is easy to access from the command line, i.e. a directory that is not nested too deep in your file tree.)

Lastly, use the following command
```bash
git clone <URL>
```
by replacing `<URL>` with the URL you copied earlier. (If you do not know how to paste text into the terminal you are using, you will need to look that up, as it varies depending on the terminal app you are using.)

### 3. Download the `config.ini` file from the SharedFolder (in Google Drive).

You should now have a directory on your PC that contains your local repo.

The next step is to go to the tech committee's SharedFolder in Google Drive. If you do not already have access to the SharedFolder, then go to the OHI/O Discord server and check the description for the `#tech-general` text channel. There will be a link that you can use to request access to the SharedFolder.

In the SharedFolder will be a file named `config.ini`. (You might need to check a subdirectory to find the file.) You must download this file **to the root directory of your local repo**, which you cloned in step 2.

<ins>**IMPORTANT:** The `config.ini` file has some sensitive information in it. Do **NOT** share the file with anyone outside of the organization!</ins>

### 4. Create a virtual environment.

In a terminal window, navigate to the root directory of your local repo. (This is where your `config.ini` file should be after step 3.)

You should now run the following command
```bash
python -m venv venv
```
to create a virtual environment in your local repo.

(As an aside, [the venv article in the Python docs](https://docs.python.org/3/library/venv.html) contains some information that you might find useful for steps 4-6.)

A virtual environment ("venv" for short) is a way for us to separate the dependencies of different Python projects from each other. After you create and activate a venv, any libraries you install will be stored in the venv. This helps prevent any issues that might be caused by conflicting dependencies for other Python projects.

### 5. Activate the venv.

There should now be a subdirectory named `venv` in your local repo, which will store all of the files related to the venv you created in step 4. You now need to activate the venv in order to use it.

If you are using the Command Prompt (`cmd.exe`) terminal on Windows, use the following command:
```batch
venv\Scripts\activate.bat
```

If you are using the Git Bash terminal on Windows, or are using the default terminal for Mac or Linux, use the following command:
```bash
venv/bin/activate
```

If neither command works for you, you can look at all of the alternate commands at [the Python doc's venv article](https://docs.python.org/3/library/venv.html#how-venvs-work).

If the venv was successfully activated, you should see "`(venv)`" before each terminal prompt.

### 6. Install dependencies/libraries.

While your venv is activated, you can install all of the dependencies for the bot by running the following command:
```bash
pip install -r requirements.txt
```

Wait a moment for all of the dependencies to be downloaded and installed. You will see your terminal prompt again when the installation process is finished.

### 7. Try running the bot.

You should now be able to try running the bot.  In order to start the bot, you need to run the [`start.py`](start.py) script. You can do this by opening a terminal window, navigating to the directory where the repo is, and then typing the following command:
```bash
python start.py
```

Once you see that the bot has finished logging in, you can try using some slash commands in the test Discord server.

To terminate the bot, type `CTRL` + `C` in the terminal (regardless of the OS you are using).

### Additional resources:

And that completes the setup process! You can now edit files, commit and push changes to your fork, and then open a pull request to merge your changes into the production code.

To learn more about using Git and GitHub, check out the following resources:
- [An Intro to Git and GitHub for Beginners](https://product.hubspot.com/blog/git-and-github-tutorial-for-beginners) by HubSpot. A good place to start for those with limited prior experience.
- [git - the simple guide](https://rogerdudler.github.io/git-guide/) covers some basic commands you will use very often.
- [The GitHub Docs](https://docs.github.com/en) has articles that cover everything you need to know about using GitHub.
- [The Pro Git ebook](https://git-scm.com/book/en/v2), which is completely free to access online. Has very comprehensive information about Git.

To learn more about using Python, check out the following resources:
- [The Python docs](https://docs.python.org/3/) has comprehensive information about Python, both for the programming language itself and some common tools you will use when working with Python projects.
- [Discord.py](https://discordpy.readthedocs.io/en/stable/) is the main library we use for the bot's code. It is worth referencing the library's docs while you are writing code for the bot.
