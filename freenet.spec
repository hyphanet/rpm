Name: freenet
Summary: The Freenet Reference Implementation
Version: 0.7
Release: 1
License: GPL
Group: Networking/Daemons
Vendor: The Freenet Project
URL: http://www.freenetproject.org/
BuildRoot: %{_tmppath}/%{name}-%{version}root

Packager: robert@freenetproject.org
# Loosely based on a freenet.spec for 0.5 by Matthew Li

#NB: This is just the skeleton, the jars are downloaded at rpm-build time, but this
#    contains an ssl-cert so we know it's origin. Therefore, it is a starting point (not fetched).
Source: http://downloads.freenetproject.org/alpha/installer/freenet07.tar.gz

%define prefix /usr
%define fproxy_port 8888

#Because we will likely get some wrappers for other arch's let's turn this off.
#Otherwise we could remove the other wrapper binaries (x86/ppc/64-bit...).
AutoReqProv: no
Requires: java
BuildRequires: java


%description
A daemon that transfers and caches data for Freenet: a free, anonymous,
survivable, scalable, and secure data publication network.

Because of the nature of freenet, this application must keep itself update-to-date,
but does so over the same network that it provides.

After installing the rpm, you must visit: http://localhost:%{fproxy_port}/
and answer some questions there before it will begin trying to connect to
the network.

%install
rm -rf $RPM_BUILD_ROOT
mkdir  $RPM_BUILD_ROOT
cd     $RPM_BUILD_ROOT

mkdir -p $RPM_BUILD_ROOT/%{prefix}/freenet/plugins
mkdir -p var/log
mkdir -p etc

pushd $RPM_BUILD_ROOT/%{prefix}
tar xzf %{SOURCE0}
cd freenet

#what follows is taken/adapted from first-run script: freenet/bin/run1.sh
CAFILE="startssl.pem"
JOPTS="-Djava.net.preferIPv4Stack=true"
OS="`uname -s`"

echo Downloading needed files from freenet project...
java $JOPTS -jar bin/sha1test.jar update.sh "." $CAFILE
java $JOPTS -jar bin/sha1test.jar wrapper_$OS.zip . "$CAFILE"
java $JOPTS -jar bin/uncompress.jar wrapper_$OS.zip .
rm -f wrapper_$OS.*
java $JOPTS -jar bin/sha1test.jar freenet-stable-latest.jar "." $CAFILE
java $JOPTS -jar bin/sha1test.jar freenet-ext.jar "." $CAFILE 
#FIXME: plugins must have moved... :(
#java $JOPTS -jar bin/sha1test.jar plugins/JSTUN.jar.url plugins $CAFILE
#java $JOPTS -jar bin/sha1test.jar plugins/UPnP.jar.url  plugins $CAFILE
java $JOPTS -jar bin/sha1test.jar seednodes.fref "." $CAFILE

cat - >> bin/crontab <<EOF
@restart %{prefix}/freenet/run.sh start
EOF

# used to manually update through conventional network if there is a network failure
chmod a+rx "./update.sh"
chmod u+x bin/* lib/*
ln -s freenet-stable-latest.jar freenet.jar

# bug: update.sh expects sha1test.jar to be in upper directory...
cp -v bin/sha1test.jar .

cat -> freenet.ini <<EOF
node.updater.enabled=true
node.updater.autoupdate=true
fproxy.enabled=true
fproxy.port=%{fproxy_port}
fcp.enabled=true
fcp.port=9481
EOF

#sha hash files are not needed after install; will reappear if updated..
rm -f *.sha1

popd # %{prefix}/freenet

ln -s %{prefix}/freenet/freenet.ini etc/freenet.ini

#FIXME: plugins
#echo "pluginmanager.loadplugin=JSTUN;UPnP" >> freenet.ini

#???: java -cp $RPM_BUILD_ROOT/%{prefix}/var/spool/freenet.jar freenet.config.Setup --silent $RPM_BUILD_ROOT/etc/freenet.ini

ln -s %{prefix}/freenet/logs/freenet-latest.log var/log/freenet

mkdir -p etc/init.d
cat - > etc/init.d/freenet <<"EOF"
#!/bin/bash
#chkconfig: 35 90 13
#description: %{summary}
#$Id$
su - freenet -c "%{prefix}/freenet/run.sh $*" < /dev/null
EOF
chmod 755 etc/init.d/freenet

%pre
if [ "$1" = 1 ]; then
   id freenet 2>/dev/null || useradd -M -d %{prefix}/freenet freenet
fi

%post
if [ "$1" = 1 ]; then
  # Sadly, a crontab with @restart doesn't work for me... :(
  #crontab -u freenet %{prefix}/freenet/bin/crontab
  /sbin/chkconfig freenet on
  /etc/init.d/freenet start && echo "Freenet should be accessible via http://localhost:%{fproxy_port}/"
fi

%preun
/etc/init.d/freenet stop
/sbin/chkconfig freenet off

%postun
if [ "$1" = 0 ]; then
	crontab -u freenet -r
	userdel freenet
else
  /etc/init.d/freenet restart
fi

%files
%defattr (-, freenet, freenet)
%{prefix}/freenet
/var/log/freenet
/etc/freenet.ini
/etc/init.d/freenet
