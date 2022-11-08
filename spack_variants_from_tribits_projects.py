import xml.etree.ElementTree as ET
tree = ET.parse('../../Compadre/trilinos-test-small/build/out.xml')
root = tree.getroot()


# register all packages as variants or conditional variants
spack_var_str = str()
spack_disable_var_str = str()
spack_noncond_var_str = str()
spack_cond_var_str = str()
parent_package_variants = []
nonparent_package_variants = []
all_package_variants = []
exclude_name_list = []#"ParentPackage", "TrilinosInstallTests", "TrilinosATDMConfigTests"]
exclude_dir_list = []#"commonTools",]
exclude_type = ["EX",]
for package in root:
    parent = package.find("ParentPackage")
    if package.get("name") not in exclude_name_list \
            and not any ([ptype==package.get("type") for ptype in exclude_type]) \
            and not any([val in package.get("dir") for val in exclude_dir_list]):
        all_package_variants.append(package.get("name"))
        if (parent.get("value")==""):
            parent_package_variants.append(package.get("name"))
            spack_noncond_var_str += "variant('" + package.get("name").lower() + "', default=False, description='Enable Trilinos package " + package.get("name") + "')\n"
        else:
            nonparent_package_variants.append(package.get("name"))
            spack_cond_var_str += "variant('" + package.get("name").lower() + "', default=False, description='Enable Trilinos subpackage " + package.get("name") + "')\n"
        spack_var_str += "variant('" + package.get("name").lower() + "', default=False)\n"

print("# Trilinos parent packages")
print(spack_noncond_var_str.replace("aztecoo","aztec"))
print("# Trilinos subpackages")
print(spack_cond_var_str.replace("aztecoo","aztec"))

# example: +tpetra turns on +tpetracore (and all other subpackages) but +tpetra doesn't require +tpetra be turned on
# create all package dependencies
spack_parent_dep_str = str()
for pkg in root:
    if pkg.get("type")!="EX":
        pp = pkg.find("ParentPackage")
        if pp.get("value")!="":
            spack_parent_dep_str += "conflicts('~" + pkg.get("name").lower() + "', when='+" + pp.get("value").lower() + "')\n"
print("# parent packages (if enabled) enable all subpackages")
print(spack_parent_dep_str.replace("aztecoo","aztec"))


# create all package dependencies
spack_req_dep_str = str()
for pkg in root:
    if pkg.get("type")!="EX":
        fields_to_append = ("LIB_REQUIRED_DEP_PACKAGES", "TEST_REQUIRED_DEP_PACKAGES")
        for field in fields_to_append:
            req_pkgs = pkg.find(field)
            if req_pkgs.get("value")!=None:
                for req_pkg in req_pkgs.get("value").split(","):
                    for pkg2 in root:
                        if pkg2.get("name")==req_pkg and pkg2.get("type")!="EX":
                            spack_req_dep_str += "conflicts('~" + req_pkg.lower() + "', when='+" + pkg.get("name").lower() + "')\n"
                            break
print("# register required package dependencies")
print(spack_req_dep_str.replace("aztecoo","aztec"))

# create all package dependencies
spack_opt_dep_str = str()
spack_opt_alt_dep_str = str()
for pkg in root:
    if pkg.get("type")!="EX":
        fields_to_append = ("LIB_OPTIONAL_DEP_PACKAGES", "TEST_OPTIONAL_DEP_PACKAGES")
        for field in fields_to_append:
            req_pkgs = pkg.find(field)
            if req_pkgs.get("value")!=None:
                for req_pkg in req_pkgs.get("value").split(","):
                    for pkg2 in root:
                        if pkg2.get("name")==req_pkg and pkg2.get("type")!="EX":
                            spack_opt_alt_dep_str += "    conflicts('~" + req_pkg.lower() + "', when='+" + pkg.get("name").lower() + "')\n"
                            break

print("# register OPTIONAL package dependencies")
print("with when('+all_optional_packages'):\n")
print(spack_opt_alt_dep_str.replace("aztecoo","aztec"))

# create all TPL requirements
spack_tpl_dep_str = str()
auto_on_tpls = ("blas", "lapack")
for pkg in root:
    if pkg.get("type")!="EX":
        fields_to_append = ("LIB_REQUIRED_DEP_TPLS", "TEST_REQUIRED_DEP_TPLS")
        for field in fields_to_append:
            req_pkgs = pkg.find(field)
            if req_pkgs.get("value")!=None:
                for req_pkg in req_pkgs.get("value").split(","):
                    if req_pkg.lower() not in auto_on_tpls:
                        spack_tpl_dep_str += "depends_on('+" + req_pkg.lower() + "', when='+" + pkg.get("name").lower() + "')\n"
#print("# register required package TPL dependencies")
#print(spack_tpl_dep_str.replace("aztecoo","aztec").replace("netcdf","netcdf-c"))

## create all TPL requirements
#spack_tpl_opt_dep_str = str()
#auto_on_tpls = ("blas", "lapack")
#for pkg in root:
#    if pkg.get("type")!="EX":
#        fields_to_append = ("LIB_REQUIRED_DEP_TPLS", "TEST_REQUIRED_DEP_TPLS")
#        for field in fields_to_append:
#            req_pkgs = pkg.find(field)
#            if req_pkgs.get("value")!=None:
#                for req_pkg in req_pkgs.get("value").split(","):
#                    if req_pkg.lower() not in auto_on_tpls:
#                        spack_tpl_opt_dep_str += "depends_on('+" + req_pkg + "', when='+" + pkg.get("name") + "')\n"
#print("# register OPTIONAL package TPL dependencies")
#print(spack_tpl_opt_dep_str)
