/**
 * GigProcessor.gs — Sin Chonies Google Apps Script
 * 
 * Trigger: Time-driven, every 5 minutes
 * Scans all upcoming calendar events and creates a Drive folder
 * for each new gig with a Notes doc and Google Maps link.
 * Tracks processed events via PropertiesService to avoid duplicates.
 * 
 * Calendar ID: ff06ebd9ad605cb6be2fd790bd0d781e74637020cd96f94bd838248fd6190ef3
 */

function createFolderFromNewEvent(e) {
  var parentFolderId = '1-BzXppt9FJ6gaQYMiA88Xj_9SSSBT3qU';
  var skipWords = ['alfred', 'mike', 'dave', 'nate', 'matt', 'out', 'unavailable', 'absent', 'blocked', 'vacation', 'off'];
  
  var calendarId = (e && e.calendarId) ? e.calendarId : 'ff06ebd9ad605cb6be2fd790bd0d781e74637020cd96f94bd838248fd6190ef3@group.calendar.google.com';
  
  var calendar = CalendarApp.getCalendarById(calendarId);
  Logger.log('Calendar: ' + (calendar ? calendar.getName() : 'NOT FOUND'));
  
  var now = new Date();
  var futureDate = new Date(now.getTime() + 31536000000);
  var events = calendar.getEvents(now, futureDate);
  Logger.log('Total upcoming events: ' + events.length);
  
  var parentFolder = DriveApp.getFolderById(parentFolderId);
  var props = PropertiesService.getScriptProperties();
  var processedIds = props.getProperty('processedEventIds') || '';
  processedIds = processedIds ? processedIds.split(',') : [];

  var newProcessed = [];
  for (var i = 0; i < events.length; i++) {
    var event = events[i];
    var eventId = event.getId();
    var title = event.getTitle();
    var titleLower = title.toLowerCase();
    
    var isMemberOut = false;
    for (var j = 0; j < skipWords.length; j++) {
      if (titleLower.indexOf(skipWords[j]) !== -1) {
        isMemberOut = true;
        break;
      }
    }
    if (isMemberOut) continue;
    
    if (processedIds.indexOf(eventId) !== -1) continue;
    
    var folderName = title + ' - ' + event.getStartTime().toLocaleDateString();
    var existingFolders = parentFolder.searchFolders('title = "' + folderName + '"');
    
    if (!existingFolders.hasNext()) {
      var newFolder = parentFolder.createFolder(folderName);
      Logger.log('Created folder: ' + folderName);
      var desc = event.getDescription() || 'No notes provided.';
      var loc = event.getLocation();
      var locData = '';
      
      if (loc) {
        var mapUrl = 'https://www.google.com/maps/search/?api=1&query=' + encodeURIComponent(loc);
        locData = 'Venue/Location: ' + loc + '\nGoogle Maps: ' + mapUrl + '\n\n';
      } else {
        locData = 'Venue/Location: Not specified in calendar event.\n\n';
      }

      var doc = DocumentApp.create(title + ' - Notes');
      doc.getBody().setText(locData + 'Notes:\n' + desc);
      doc.saveAndClose();
      DriveApp.getFileById(doc.getId()).moveTo(newFolder);
      Logger.log('Done: ' + folderName);
    } else {
      Logger.log('Folder already exists: "' + folderName + '"');
    }
    
    newProcessed.push(eventId);
  }
  
  var allProcessed = processedIds.concat(newProcessed);
  if (allProcessed.length > 500) {
    allProcessed = allProcessed.slice(allProcessed.length - 500);
  }
  props.setProperty('processedEventIds', allProcessed.join(','));
  Logger.log('Processed ' + newProcessed.length + ' new events. Total tracked: ' + allProcessed.length);
}
