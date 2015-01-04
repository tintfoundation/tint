var Path = function(path) {
   var normalize = null, normpath = null;

   normalize = function(p) {
      if(p === '')
	 p = '/';

      if(p.charAt(0) !== '/')
	 p = '/' + p;

      if(p.length > 1 && p.charAt(p.length - 1) === '/')
	 p = p.substr(0, p.length - 1);

      return p;
   };

   normpath = normalize(path);
   return {
      path: normpath,
      length: normpath.length,
      join: function(opath) {
	 return Path(normpath + normalize(opath));
      }
   };
};

var Storage = function(log, http, host, prefix) {
   return {
      uri: function(path) {
	 return '/api/v1/storage/' + host + path;
      },
      get: function(path, callback) {
	 path = prefix.join(path).path;
	 log.debug('Getting ' + path + ' on ' + host);
	 http.get(this.uri(path)).success(function (r) { callback(r.result); });
      },      
      ls: function(path, offset, length, callback) {
	 path = prefix.join(path).path + '/';
	 log.debug('Getting ' + path + ' on ' + host + ' (offset ' + offset + ', length ' + length + ')');
	 http.get(this.uri(path), {offset: offset, length: length}).success(function (r) { callback(r.result); });
      },
      set: function(path, value, callback) {
	 path = prefix.join(path).path;
	 log.debug('Setting ' + path + ' on ' + host + ' to "' + value + '"');
	 http.post(this.uri(path), {value: value}).success(function (r) { if(callback) callback(r.result); });
      },      
      push: function(path, value, callback) {
	 path = prefix.join(path).path + '/';
	 log.debug('Pushing ' + path + ' on ' + host + ' to "' + value + '"');
	 http.post(this.uri(path), {value: value}).success(function(r) {
							      if(callback)
								 callback(r.result.substr(prefix.length));
							   });
      }
   };
};

var tint = angular.module('tint', []);
tint.service('tint.app', ["$log", "$http", function($log, $http) {
			     return {
				init: function(host, myid, appname) {
				   var prefix = Path(myid).join('apps').join(appname);
				   return Storage($log, $http, host, prefix);
				}
			     };
			  }]);
			     
