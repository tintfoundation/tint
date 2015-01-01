/*
var storage = Storage("1231o2310923109231023...");

storage.get("/1102931309123.../apps/chat/

*/

var Path = function(path) {
   var normalize = null;

   normalize = function(p) {
      if(p === '')
	 path = '/';

      if(p.charAt(0) !== '/')
	 p = '/' + p;

      if(p.length > 1 && path.charAt(path.length - 1) === '/')
	 p = p.substr(0, p.length - 2)

      return p;
   };

   return {
      path: normalize(path),
      join: function(opath) {
	 return Path(this.path + normalize(opath));
      }
   };
};

var Storage = function(host, prefix) {
   prefix = prefix || "";
   return {
      host: host,
      ls: function(path, offset, length, callback) {

      },
      set: function(path, value) {

      },
      get: function(path) {

      },
      push: function(path, value) {

      }
   };
};

var AppStorage = function(host, myid, appname) {
   return Storage(host, Path(myid).join(appname).path);
};