<div align="center">

# pyDatalink by Septentrio
## AUTHORS
  
| Name | GitHub |
|------|--------|
| Arno Balois| <a href="https://github.com/Arno-Balois">Arno-Balois</a> </br> | 

## MAINTAINER
  
| GitHub |
|--------|
| <a href="https://github.com/septentrio-users">septentrio-users</a> </br> |    

## DO YOU HAVE ANY QUESTIONS? CONTACT SEPTENTRIO SUPPORT TEAM

| <a href="https://web.septentrio.com/GH-SSN-support ">Septentrio Support Page</a>|
|---|

## SEPTENTRIO LINKS FOR USERS
 
| Contact                                                                          | Septentrio Home Page                                                        |
|----------------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| <a href="https://web.septentrio.com/GH-SSN-contact ">Septentrio Contact Page</a> | <a href="https://web.septentrio.com/UBL-SSN-home">Septentrio Home Page</a> |


</div>

## TABLE OF CONTENTS

<!--ts-->
* [What is Data Link ?](#what-is-pydatalink)
* [Getting Started](#Getting-Started)
* [Is the project Open Source?](#is-the-project-open-source)
* [User Guide](#user-guide)
  
<!--te-->


# What is DataLink 

Data Link is a software tool developed by Septentrio and is available as part of the RxTools suite. RxTools is a collection of GUI tools designed for monitoring and configuring Septentrio's receivers, logging data and downloading SBF data files, as well as analyzing and converting SBF data files to different formats.

Data Link, within the RxTools suite, serves as a graphical communication terminal that enables users to establish connections with multiple devices and facilitate data transfer between them.
<div align="center">
<img src="doc_sources/pyDatalink.PNG" width="75%">
</div>
<br>


# Installation
As pyDatalink app is entirely developed with python, you must first install python and all its dependencies.
## Install Python 
### Unix Users

1 - Update Package index
```
sudo apt update 
```
2 - Install Python
```
sudo apt-get install python3 pip
```
### Windows Users
Download the latest version of the Python executable installer for Windows from the <a href="https://www.python.org/downloads/"> the official Python downloads page </a>.

Or open the windows store and search for python and click on install


## Install project

Once you've installed python, all you have to do is download the source code and launch the application. 

### Using git clone
```
git clone https://github.com/septentrio-gnss/DataLink.git
cd DataLink
```
### using GitHub
 - First click on **code**.<br>
 - Then click on **dowload Zip**
### (Optional) Create a Virtual environement
This will allow you to create a contained workspace where every python package will be installed
```
python -m venv venv
source venv/bin/activate
```
### Install Python packages 
```
pip install -r requirements.txt
```
### Run pyDatalink 

By default pyDatalink run as a Graphical interface
```
python pyDatalink.py
```

<br>

# How to use guides

As this project is open source, two guides are available: 
- a guide for users which describe all the available functionnalities
- a developer's guide which explains how the program is structured and how it works 

The purpose of the user guide is to explain how to install the application, how to use it and also to present the various functionnalities. 

<div align="center">

| <a href="https://github.com/septentrio-gnss/Septentrio-PyDataLink/tree/main/user">Go to User Manual</a> |
|---|

</div>


The purpose of the development guide is to explain how the code is structured, how the programme works and how it was made. This guide is mainly intended for people who want to keep the programme up to date. 

<div align="center">

| <a href="https://github.com/septentrio-gnss/Septentrio-PyDataLink/tree/main/dev">Go to developper Guide</a> |
|---|

</div>



