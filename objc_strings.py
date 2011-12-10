#!/usr/bin/env python

# Nicolas Seriot
# 2011-05-09 - 2011-12-10
# https://github.com/nst/objc_strings/

"""
Goal: helps Cocoa applications localization by detecting unused and missing keys in '.strings' files

Input: path of an Objective-C project

Output:
    1) warnings for untranslated strings in *.m
    2) warnings for unused keys in Localization.strings

Typical usage: $ python objc_strings.py /path/to/obj_c/project

Xcode integration:
    - copy objc_strings.py at the root of your project
    - add a 'Run Script' build phase to your target
        - shell: /bin/sh
        - script: ${SOURCE_ROOT}/objc_strings.py
"""

import sys
import os
import re
import codecs

def warning(file_path, line_number, message):
    print "%s:%d: warning: %s" % (file_path, line_number, message)

def error(file_path, line_number, message):
    print "%s:%d: error: %s" % (file_path, line_number, message)

m_paths_and_line_numbers_for_key = {} # [{'k1':(('f1, n1'), ('f1, n2'), ...), ...}]
s_paths_and_line_numbers_for_key = {} # [{'k1':(('f1, n1'), ('f1, n2'), ...), ...}]

def language_code_in_strings_path(p):
    m = re.search(".*/(.*?.lproj)/", p)
    if m:
        return m.group(1)
    return None   

def key_in_string(s):
    m = re.search("\"(.*?)\"", s)
    if not m:
        return None
    
    key = m.group(1)
    
    if key.startswith("//") or key.startswith("/*"):
        return None
    
    return key

def keys_set_in_strings_file_at_path(p):
    
    for encoding in ('utf-8', 'utf-16'):        
        try:
            keys = set()
            f = codecs.open(p, encoding=encoding)
            
            line = 0
            for s in f.xreadlines():
                line += 1
                
                key = key_in_string(s)
                
                if not key:
                    continue
                
                keys.add(key)
                
                if key not in s_paths_and_line_numbers_for_key:
                    s_paths_and_line_numbers_for_key[key] = set()
                s_paths_and_line_numbers_for_key[key].add((p, line))
            
            return keys
        
        except:
            pass
    
    return None

def localized_strings_at_path(p):
    f = open(p)
    
    keys = set()
    
    line = 0
    for s in f.xreadlines():
        line += 1
        m = re.search("NSLocalizedString\(@\"(.*?)\"", s)
        if not m:
            continue
        
        key = m.group(1)
    
        keys.add(key)

        if key not in m_paths_and_line_numbers_for_key:
            m_paths_and_line_numbers_for_key[key] = set()
        m_paths_and_line_numbers_for_key[key].add((p, line))
    
    return keys

def paths_with_files_passing_test_at_path(test, path):
    for root, dirs, files in os.walk(path):
        for p in (os.path.join(root, f) for f in files if test(f)):
            yield p

def keys_set_in_code_at_path(path):
    m_paths = paths_with_files_passing_test_at_path(lambda f:f.endswith('.m'), path)
    
    localized_strings = set()
    
    for p in m_paths:
        keys = localized_strings_at_path(p)
        
        localized_strings.update(keys)
    
    return localized_strings

def show_untranslated_keys_in_project(project_path):
    
    if not project_path or not os.path.exists(project_path):
        error("", 0, "bad project path:%s" % project_path)
        return
    
    keys_set_in_code = keys_set_in_code_at_path(project_path)

    strings_paths = paths_with_files_passing_test_at_path(lambda f:f == "Localizable.strings", project_path)
    
    for p in strings_paths:
        keys_set_in_strings = keys_set_in_strings_file_at_path(p)
        
        missing_keys = keys_set_in_code - keys_set_in_strings
        unused_keys = keys_set_in_strings - keys_set_in_code

        language_code = language_code_in_strings_path(p)
        
        for k in missing_keys:
            message = "missing key in %s: \"%s\"" % (language_code, k)
            
            for (p_, n) in m_paths_and_line_numbers_for_key[k]:
                warning(p_, n, message)

        for k in unused_keys:
            message = "unused key in %s: \"%s\"" % (language_code, k)
            
            for (p, n) in s_paths_and_line_numbers_for_key[k]:
                warning(p, n, message)

def main():
    
    project_path = None
    
    if 'PROJECT_DIR' in os.environ:
        project_path = os.environ['PROJECT_DIR']
    elif len(sys.argv) > 1:
        project_path = sys.argv[1]
    
    show_untranslated_keys_in_project(project_path)

if __name__ == "__main__":
    main()