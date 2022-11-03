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
            spack_noncond_var_str += "variant('" + package.get("name").lower() + "', default=False)\n"
            spack_disable_var_str += "variant('disable_" + package.get("name").lower() + "', default=False, sticky=True, when='+explicit_disable')\n"
        else:
            nonparent_package_variants.append(package.get("name"))
            spack_cond_var_str += "variant('" + package.get("name").lower() + "', default=False, when='+" + parent.get("value").lower() + "')\n"
            #spack_var_str += "variant('" + package.get("name").lower() + "', default=False)\n"
            #spack_disable_var_str += "variant('disable_" + package.get("name").lower() + "', default=False, sticky=True)\n"
            #spack_disable_var_str += "conflicts('+" + package.get("name").lower() + "', when='+disable_" + package.get("name").lower() + "')\n"
            spack_disable_var_str += "variant('disable_" + package.get("name").lower() + "', default=False, sticky=True, when='+explicit_disable+disable_" + package.get("name").lower() + "')\n"
        spack_var_str += "variant('" + package.get("name").lower() + "', default=False)\n"
        spack_disable_var_str += "conflicts('+" + package.get("name").lower() + "', when='+disable_" + package.get("name").lower() + "')\n"

print(spack_noncond_var_str.replace("aztecoo","aztec"))
print(spack_cond_var_str.replace("aztecoo","aztec"))
#print(spack_var_str)
print(spack_disable_var_str.replace("aztecoo","aztec"))
#print(spack_cond_var_str)


# get all dependencies and their parents
def get_deps_for_package(root, package_name):
    # build up all optional dependencies
    def get_down_deps_for_package(root, package_name):
    
        deps = set()
        package = None
        for pkg in root:
            if pkg.get("name").lower()==package_name.lower() and pkg.get("type")!="EX":
                package = pkg
                break
            elif pkg.get("name").lower()==package_name.lower():
                return deps
        assert package is not None, "Package {0} not found".format(package_name)
    
        fields_to_append = ("LIB_REQUIRED_DEP_PACKAGES", "LIB_OPTIONAL_DEP_PACKAGES", "TEST_REQUIRED_DEP_PACKAGES", "TEST_OPTIONAL_DEP_PACKAGES")
        for field in fields_to_append:
            req_pkgs = package.find(field)
            if req_pkgs.get("value")!=None:
                for req_pkg in req_pkgs.get("value").split(","):
                    deps |= get_down_deps_for_package(root, req_pkg)
    
        return set([package_name,]) | deps
    
    # get parents and parents of parents of all dependencies
    def get_up_deps_for_package(root, dep_set):
        new_dep_set = set()
        for dep in dep_set:
            package = None
            for pkg in root:
                if pkg.get("name").lower()==dep.lower() and pkg.get("type")!="EX":
                    package = pkg
                    break
                elif pkg.get("name").lower()==dep.lower():
                    return deps
            assert package is not None, "Package {0} not found".format(dep)
            pp = package.find("ParentPackage")
            if pp.get("value")!="":
                if pp.get("value") not in dep_set:
                    new_dep_set |= get_up_deps_for_package(root, set([pp.get("value"),]))
        return new_dep_set | dep_set

    dep_set = get_down_deps_for_package(root, package_name)
    dep_set = get_up_deps_for_package(root, dep_set)
    return dep_set

## get list of all packages enabled by turning on a package
## ST only used if -D Trilinos_SECONDARY_TESTED_CODE:BOOL=ON
## EX never counted
#dep_set = get_deps_for_package(root, "MueLu")
#print(len(dep_set), dep_set)
#t=set(["KokkosCore","KokkosContainers","KokkosAlgorithms","Kokkos","TeuchosCore","TeuchosParser","TeuchosParameterList","TeuchosComm","TeuchosNumerics","TeuchosRemainder","TeuchosKokkosCompat","TeuchosKokkosComm","Teuchos","KokkosKernels","RTOp","Sacado","Epetra","Zoltan","Shards","Triutils","EpetraExt","TpetraTSQR","TpetraCore","Tpetra","TrilinosSS","ThyraCore","ThyraEpetraAdapters","ThyraEpetraExtAdapters","ThyraTpetraAdapters","Thyra","Xpetra","Isorropia","AztecOO","Galeri","Amesos","Pamgen","Zoltan2Core","Ifpack","ML","Belos","ShyLU_NodeHTS","ShyLU_NodeTacho","ShyLU_Node","Amesos2","Anasazi","Ifpack2","Stratimikos","Teko","Intrepid2","MueLu"])
#print(len(t), t)
#print("dep-t", dep_set - t)
#print("t-dep", t-dep_set)


## check if all required dependencies are in ...
#for package in root:
#    req_pkgs = package.find("LIB_REQUIRED_DEP_PACKAGES")
#    if req_pkgs.get("value")!=None:
#        for req_pkg in req_pkgs.get("value").split(","):
#            #print(package.get("name"), req_pkg, req_pkg in parent_package_variants)
#            if req_pkg not in package_variants:
#                print(package.get("name"), req_pkg, req_pkg in package_variants)
## every required package is in the existing list of PT packages except for:
##SEACASSVDI
##SEACASPLT
##Gtest

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
        #fields_to_append = ("LIB_OPTIONAL_DEP_PACKAGES", "TEST_OPTIONAL_DEP_PACKAGES")
        #for field in fields_to_append:
        #    req_pkgs = pkg.find(field)
        #    if req_pkgs.get("value")!=None:
        #        for req_pkg in req_pkgs.get("value").split(","):
        #            for pkg2 in root:
        #                if pkg2.get("name")==req_pkg and pkg2.get("type")!="EX":
        #                    spack_dep_str += "with when('+explicit_disable'):\n"
        #                    spack_dep_str += "    conflicts('~" + req_pkg.lower() + "', when='+" + pkg.get("name").lower() + "~disable_" + req_pkg.lower() + "')\n"
        #                    spack_dep_str += "with when('~explicit_disable'):\n"
        #                    spack_dep_str += "    conflicts('~" + req_pkg.lower() + "', when='+" + pkg.get("name").lower() + "')\n"
        #                    break
        #pp = pkg.find("ParentPackage")
        #if pp.get("value")!="":
        #    spack_dep_str += "conflicts('~" + pp.get("value").lower() + "', when='+" + pkg.get("name").lower() + "')\n"
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
                            #spack_dep_str += "with when('+explicit_disable'):\n"
                            spack_opt_dep_str += "    conflicts('~" + req_pkg.lower() + "', when='+" + pkg.get("name").lower() + "~disable_" + req_pkg.lower() + "')\n"
                            #spack_dep_str += "with when('~explicit_disable'):\n"
                            spack_opt_alt_dep_str += "    conflicts('~" + req_pkg.lower() + "', when='+" + pkg.get("name").lower() + "')\n"
                            break
print("with when('+explicit_disable'):\n")
print(spack_opt_dep_str.replace("aztecoo","aztec"))
print("with when('~explicit_disable'):\n")
print(spack_opt_alt_dep_str.replace("aztecoo","aztec"))

# create all package dependencies
spack_parent_dep_str = str()
for pkg in root:
    if pkg.get("type")!="EX":
        pp = pkg.find("ParentPackage")
        if pp.get("value")!="":
            spack_parent_dep_str += "conflicts('~" + pp.get("value").lower() + "', when='+" + pkg.get("name").lower() + "')\n"
print(spack_parent_dep_str)

# create all TPL requirements
spack_tpl_dep_str = str()
auto_on_tpls = ("blas", "lapack")
for pkg in root:
    if pkg.get("type")!="EX":
        fields_to_append = ("LIB_REQUIRED_DEP_TPLS",)
        for field in fields_to_append:
            req_pkgs = pkg.find(field)
            if req_pkgs.get("value")!=None:
                for req_pkg in req_pkgs.get("value").split(","):
                    if req_pkg.lower() not in auto_on_tpls:
                        spack_tpl_dep_str += "depends_on('+" + req_pkg.lower() + "', when='+" + pkg.get("name").lower() + "')\n"
#print(spack_tpl_dep_str)

## create all TPL requirements
#spack_tpl_opt_dep_str = str()
#auto_on_tpls = ("blas", "lapack")
#for pkg in root:
#    if pkg.get("type")!="EX":
#        fields_to_append = ("LIB_OPTIONAL_DEP_TPLS",)
#        for field in fields_to_append:
#            req_pkgs = pkg.find(field)
#            if req_pkgs.get("value")!=None:
#                for req_pkg in req_pkgs.get("value").split(","):
#                    if req_pkg.lower() not in auto_on_tpls:
#                        spack_tpl_opt_dep_str += "depends_on('+" + req_pkg + "', when='+" + pkg.get("name") + "')\n"
#print(spack_tpl_opt_dep_str)


#print("parents:",parent_package_variants)
#print("all:",package_variants)

# register all parent packages as variants
