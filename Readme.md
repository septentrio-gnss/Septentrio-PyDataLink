<div align="center">

# pyDatalink by Septentrio

**Note : This tool is currently under testing. Feel free to provide feedback <a href="https://forms.office.com/e/UqdAs4hfF3 ">here</a> .**
## AUTHORS
  
| Name | GitHub |
|------|--------|
| Arno Balois| <a href="https://github.com/Arno-Balois">Arno-Balois</a> </br> | 

## MAINTAINER
  
| GitHub |
|--------|
| <a href="https://github.com/septentrio-users">septentrio-users</a> </br> |    

## DO YOU HAVE ANY QUESTIONS? CONTACT SEPTENTRIO SUPPORT TEAM

| <a href="https://web.septentrio.com/GH-SSN-support ">Septentrio Support Page</a></br>PyDataLink is not officially supported by Septentrio however Septentrio can provide great help around Septentrio GNSS receivers|
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

Data Link is a software tool developed by <a href="https://web.septentrio.com/GH-SSN-home">Septentrio</a> and is available as part of the RxTools suite. RxTools is a collection of GUI tools designed for monitoring and configuring <a href="https://web.septentrio.com/GH-SSN-home">Septentrio's</a> GNSS receivers, logging data and downloading SBF data files, as well as analyzing and converting SBF data files to different formats.

<a href"https://web.septentrio.com/GH-SSN-home">Septentrio</a> is a leading provider of high-precision GNSS solutions known for delivering robust and reliable positioning technology across various industries.

Data Link, within the RxTools suite, serves as a graphical communication terminal that enables users to establish connections with multiple devices and facilitate data transfer between them.


# What is PyDataLink
Pydatalink is an application whose functions are similar to RxTools' Datalink, but whose special feature is that it is compatible with ARM and x86 systems. The idea of recreating a data link application came from the fact that the current version of Datalink is only compatible with x86 architectures and that cross-compiling it to support other architectures is complex because of the project's various dependencies.

The second major feature of this version is that the code is entirely open source, unlike the Datalink code. The aim of making the project available as open source is to allow the community to contribute to the development of the tool in order to integrate new functionalities.
<div align="center">
<img src="doc_sources/pyDatalink.PNG" >
</div>
<br>

These are the major features of PyDataLink:
 - Connecivity for up to 6 parallel connections: TCP , UDP , Serial: Handy for GNSS receivers or other sensors/systems
 - Support for NTRIP Client including TLS support
 - Logging of data passing through the connection
 - Automatic configuration scrips at connection and/or disconnection (handy to automatically configure GNSS receivers or other sensors)
 - Terminal Display on connections
 - Redirection of data to multiple connections

While the tool has been mainly tested with Septentrio GNSS receivers, it is generic enough to work with other systems (e.g. cell modems, radios, u-blox receivers, etc).

# Installation

As pyDatalink app is entirely developed with python, you must first install python and all its dependencies.

## Install Python 
We recommend using a version of python that is 3.11.2 or higher.
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
git clone https://github.com/septentrio-gnss/Septentrio-PyDataLink.git
cd Septentrio-PyDataLink
```
### using GitHub
 - First click on **code**.<br>
 - Then click on **dowload Zip**

## Build the project 
to build and generate the executable file  , run the folowing command
```
python build.py
```
After the build is successfully completed , a executable file will be generated 

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

## Informations
### Tested Platforms
The current version of pyDatalink has been tested on the following plateform :
- Raspberry Pi OS 64bit with Desktop - kernel : 6.6 ( Raspberry pi 4)
- Windows 10 *(GUI & CMD only)*

### Tested Package version
The current version of pyDatalink has been tested with the following packages version : 
- Python 3.11.2 and 3.12.3 
- pyserial 3.5
- PySide6 6.7.0 
- PySide6_Addons 6.7.0
- PySide6_Essentials 6.7.0
- shiboken6 6.7.0
- simple-term-menu 1.6.4
- typing_extensions 4.11.0




