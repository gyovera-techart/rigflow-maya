"""Run inside Maya to install a .mod file and a RigFlow shelf button."""
from rigflow.installer import install_shelf_button, write_module_file

module_file = write_module_file()
shelf_button = install_shelf_button()
print("RigFlow module file:", module_file)
print("RigFlow shelf button:", shelf_button)
print("Restart Maya once so the new .mod file is discovered automatically.")
