#!/usr/bin/env python

import re
import subprocess
import shutil
import hashlib
import os
import argparse
import platform
import sys
import logging

import modules


def main():
    if not modules.check_key_file(args.prod_keys):
        logger_interface.error('Keys file is not valid!')
        sys.exit()

    os.system(f'{modules.hactoolnet} --keyset {args.prod_keys} --intype switchfs {args.firmware} --title 0100000000000809 --romfsdir titleid/0100000000000809/romfs/')
    with open(f'titleid/0100000000000809/romfs/file', 'rb') as get_version:
            byte_alignment = get_version.seek(0x68)
            read_version_number = get_version.read(0x6).hex().upper()
            version = (bytes.fromhex(read_version_number).decode('utf-8'))
            fork_version = version.replace('.', '_')
            logger_interface.info("Firmware version number is: %s", version)

    escompressed = 'titleid/0100000000000033/exefs/main'
    nifmcompressed = 'titleid/010000000000000f/exefs/main'
    nimcompressed = 'titleid/0100000000000025/exefs/main'
    esuncompressed = 'titleid/0100000000000033/exefs/u_main'
    nifmuncompressed = 'titleid/010000000000000f/exefs/u_main'
    nimuncompressed = 'titleid/0100000000000025/exefs/u_main'
    fat32compressed = 'titleid/0100000000000819/romfs/nx/ini1/FS.kip1'
    exfatcompressed = 'titleid/010000000000081b/romfs/nx/ini1/FS.kip1'
    fat32uncompressed = 'titleid/0100000000000819/romfs/nx/ini1/u_FS.kip1'
    exfatuncompressed = 'titleid/010000000000081b/romfs/nx/ini1/u_FS.kip1'

    logger_interface.info('Extracting ES')
    os.system(f'{modules.hactoolnet} --keyset {args.prod_keys} --intype switchfs {args.firmware} --title 0100000000000033 --exefsdir titleid/0100000000000033/exefs/')
    os.system(f'{modules.hactool} --disablekeywarns --keyset {args.prod_keys} --intype nso0 {escompressed} --uncompressed={esuncompressed}')

    logger_interface.info('Extracting NIFM')
    os.system(f'{modules.hactoolnet} --keyset {args.prod_keys} --intype switchfs {args.firmware} --title 010000000000000f --exefsdir titleid/010000000000000f/exefs/')
    os.system(f'{modules.hactool} --disablekeywarns --keyset {args.prod_keys} --intype nso0 {nifmcompressed} --uncompressed={nifmuncompressed}')

    logger_interface.info('Extracting NIM')
    os.system(f'{modules.hactoolnet} --keyset {args.prod_keys} --intype switchfs {args.firmware} --title 0100000000000025 --exefsdir titleid/0100000000000025/exefs/')
    os.system(f'{modules.hactool} --disablekeywarns --keyset {args.prod_keys} --intype nso0 {nimcompressed} --uncompressed={nimuncompressed}')

    logger_interface.info('Extracting fat32')
    os.system(f'{modules.hactoolnet} --keyset {args.prod_keys} --intype switchfs {args.firmware} --title 0100000000000819 --romfsdir titleid/0100000000000819/romfs/')
    os.system(f'{modules.hactoolnet} --keyset {args.prod_keys} --intype pk21 titleid/0100000000000819/romfs/nx/package2 --ini1dir titleid/0100000000000819/romfs/nx/ini1')
    os.system(f'{modules.hactoolnet} --keyset {args.prod_keys} --intype kip1 {fat32compressed} --uncompressed {fat32uncompressed}')

    logger_interface.info('Extracting exfat')
    os.system(f'{modules.hactoolnet} --keyset {args.prod_keys} --intype switchfs {args.firmware} --title 010000000000081b --romfsdir titleid/010000000000081b/romfs/')
    os.system(f'{modules.hactoolnet} --keyset {args.prod_keys} --intype pk21 titleid/010000000000081b/romfs/nx/package2 --ini1dir titleid/010000000000081b/romfs/nx/ini1')
    os.system(f'{modules.hactoolnet} --keyset {args.prod_keys} --intype kip1 {exfatcompressed} --uncompressed {exfatuncompressed}')

    logger_interface.info('===== Making patches for %s =====', version)


    with open(f'{esuncompressed}', 'rb') as decompressed_es_nso:
        esbuildid = modules.get_build_id(decompressed_es_nso)
        logger_interface.info('ES build ID %s', esbuildid)
        es_patch = f'{esbuildid}.ips'
        if es_patch in os.listdir(modules.ES_PATCH_DIR):
            logger_interface.warning('ES patch for version %s already exists as an .ips patch, and the build id is: %s', version, esbuildid)
        else:
            read_data = decompressed_es_nso.read()
            result = re.search(rb'.\x00\x91.{2}\x00\x94\xa0\x83\x00\xd1.{2}\xff\x97', read_data)
            if not result:
                logger_interface.error('%s ES offset not found', version)
            else:
                patch = '%06X%s%s' % (result.end(), '0004', 'E0031FAA')
                offset = '%06X' % (result.end())
                with open(os.path.join(modules.ES_PATCH_DIR, es_patch), 'wb') as text_file:
                    text_file.write(bytes.fromhex(modules.IPS_HEADER + patch + modules.IPS_FOOTER))
                logger_interface.info('%s:\nES build-id: %s\nES offset and patch at: %s', version, esbuildid, patch)


    with open(f'{nifmuncompressed}', 'rb') as decompressed_nifm_nso:
        nifmbuildid = modules.get_build_id(decompressed_nifm_nso)
        logger_interface.info('NIFM CTEST build ID %s', esbuildid)
        nifm_patch = f'{nifmbuildid}.ips'
        if nifm_patch in os.listdir(modules.NIFM_CTEST_PATCH_DIR):
            logger_interface.warning('NIFM CTEST patch for version %s already exists as an .ips patch, and the build id is: %s', version, nifmbuildid)
        else:
            read_data = decompressed_nifm_nso.read()
            result = re.search(rb'.{20}\xf4\x03\x00\xaa.{4}\xf3\x03\x14\xaa\xe0\x03\x14\xaa\x9f\x02\x01\x39\x7f\x8e\x04\xf8', read_data)
            if not result:
                logger_interface.error('%s NIFM offset not found', version)
            else:
                patch = '%06X%s%s' % (result.start(), '0014', '00309AD2001EA1F2610100D4E0031FAAC0035FD6')
                offset = '%06X' % (result.start())
                with open(os.path.join(modules.NIFM_CTEST_PATCH_DIR, nifm_patch), 'wb') as text_file:
                    text_file.write(bytes.fromhex(modules.IPS_HEADER + patch + modules.IPS_FOOTER))
                logger_interface.info('%s:\nNIFM build-id: %s\nNIFM offset and patch at: %s', version, nifm_patch, patch)


    with open(f'{nimuncompressed}', 'rb') as decompressed_nim_nso:
        nimbuildid = modules.get_build_id(decompressed_nim_nso)
        logger_interface.info('NIM build ID %s', nimbuildid)
        nim_patch = f'{nimbuildid}.ips'
        if nim_patch in os.listdir(modules.NIM_PATCH_DIR):
            logger_interface.warning('NIM patch for version %s already exists as an .ips patch, and the build id is: %s', version, nifmbuildid)
        else:
            read_data = decompressed_nim_nso.read()
            result = re.search(rb'\x80\x0f\x00\x35\x1f\x20\x03\xd5', read_data)
            if not result:
                logger_interface.e('%s NIM offset not found', version)
            else:
                patch = '%06X%s%s' % (result.end(), '0004', 'E2031FAA')
                offset = '%06X' % (result.end())
                with open(modules.NIM_PATCH_DIR + nim_patch, 'wb') as text_file:
                    text_file.write(bytes.fromhex(modules.IPS_HEADER + patch + modules.IPS_FOOTER))
                logger_interface.info('%s:\nNIM build-id: %s\nNIM offset and patch at: %s', version, nifm_patch, patch)


    with open(modules.HEKATE_PATCH_FILE) as fs_patches_object:
        fs_patches = fs_patches_object.read()

    fat32hash = hashlib.sha256(open(fat32compressed, 'rb').read()).hexdigest().upper()
    if fat32hash[:16] in fs_patches:
        logger_interface.warning('FS-FAT32 patch for version %s already exists in fs_patches.ini with the short hash of: %s', version, fat32hash[:16])
    else:
        with open(fat32uncompressed, 'rb') as fat32f:
            read_data = fat32f.read()
            result1 = re.search(rb'\x52.{3}\x52.{3}\x52.{3}\x52.{3}\x94', read_data)
            result2 = re.search(rb'\x08\x1C\x00\x12\x1F\x05\x00\x71\x41\x01\x00\x54', read_data)
            if not result1:
                logger_interface.error('%s First FS-FAT32 offset not found', version)
            elif not result2:
                logger_interface.error('%s Second FS-FAT32 offset not found', version)
            else:
                patch1 = '%06X%s%s' % (result1.end(), '0004', '1F2003D5')
                patch2 = '%06X%s%s' % (result2.start() - 0x4, '0004', 'E0031F2A')
                logger_interface.info('%s\nFirst FS-FAT32 offset and patch at: %s\nSecond FS-FAT32 offset and patch at: %s\nFS-FAT32 SHA256 hash: %s', version, patch1, patch2, fat32hash)
                with open(modules.HEKATE_FS_FILE, 'a') as fat32_hekate:
                    fat32_hekate.write(f'#FS {version}-fat32\n')
                    fat32_hekate.write(f'[FS:{fat32hash[:16]}]\n')
                    byte_alignment = fat32f.seek(result1.end())
                    fat32_hekate.write(f'.nosigchk=0:0x{result1.end()-0x100:06X}:0x4:{fat32f.read(0x4).hex().upper()},1F2003D5\n')
                    byte_alignment = fat32f.seek(result2.start() - 0x4)
                    fat32_hekate.write(f'.nosigchk=0:0x{result2.start()-0x104:06X}:0x4:{fat32f.read(0x4).hex().upper()},E0031F2A\n')
                logger_interface.info('%s:\nFS-FAT32 hash %s\n№1 FS-FAT32 offset and patch at %s\n№2 FS-FAT32 offset and patch at %s', version, fat32hash[:16], f'{result1.end()-0x100:06X}', f'{result2.start()-0x104:06X}')

    exfathash = hashlib.sha256(open(exfatcompressed, 'rb').read()).hexdigest().upper()
    if exfathash[:16] in fs_patches:
        logger_interface.warning('FS-ExFAT patch for version %s already exists in fs_patches.ini with the short hash of: %s', version, exfathash[:16])
    else:
        with open(exfatuncompressed, 'rb') as exfatf:
            read_data = exfatf.read()
            result1 = re.search(rb'\x52.{3}\x52.{3}\x52.{3}\x52.{3}\x94', read_data)
            result2 = re.search(rb'\x08\x1C\x00\x12\x1F\x05\x00\x71\x41\x01\x00\x54', read_data)
            if not result1:
                logger_interface.error('%s First FS-ExFAT offset not found', version)
            elif not result2:
                logger_interface.error('%s Second FS-ExFAT offset not found', version)
            else:
                patch1 = '%06X%s%s' % (result1.end(), '0004', '1F2003D5')
                patch2 = '%06X%s%s' % (result2.start() - 0x4, '0004', 'E0031F2A')
                logger_interface.info('%s\nFirst FS-ExFAT offset and patch at: %s\nSecond FS-ExFAT offset and patch at: %s\nFS-ExFAT SHA256 hash: %s', version, patch1, patch2, exfathash)
                with open(modules.HEKATE_FS_FILE, 'a') as exfat_hekate:
                    exfat_hekate.write(f'#FS {version}-exfat\n')
                    exfat_hekate.write(f'[FS:{exfathash[:16]}]\n')
                    byte_alignment = exfatf.seek(result1.end())
                    exfat_hekate.write(f'.nosigchk=0:0x{result1.end()-0x100:06X}:0x4:{exfatf.read(0x4).hex().upper()},1F2003D5\n')
                    byte_alignment = exfatf.seek(result2.start() - 0x4)
                    exfat_hekate.write(f'.nosigchk=0:0x{result2.start()-0x104}:0x4:{exfatf.read(0x4).hex().upper()},E0031F2A\n')
                logger_interface.info('%s:\nFS-ExFAT hash %s\n№1 FS-FAT32 offset and patch at %s\n№2 FS-ExFAT offset and patch at %s', version, exfathash[:16], f'{result1.end()-0x100:06X}', f'{result2.start()-0x104:06X}')

    modules.pack_hekate_patch()
    logger_interface.info('Packing Hekate patch is OK!')
    shutil.rmtree('titleid')


if __name__ == "__main__":
    argParser = argparse.ArgumentParser()
    argParser.add_argument("-f", "--firmware", help="firmware folder", dest="firmware", type=str, default="./firmware")
    argParser.add_argument("--keyset", "---keyseteys", help="keyfile to use", dest="prod_keys", type=str, default="./prod.keys")
    args = argParser.parse_args()

    logger_interface = logging.getLogger('make patches')
    modules.logging_configuration(logger_interface)
    sys.exit(main())